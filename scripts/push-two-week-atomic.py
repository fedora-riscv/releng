#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# push-two-week-atomic.py - An utility to sync two-week Atomic Host releases
#
# For more information about two-week Atomic Host releases please visit:
#   https://fedoraproject.org/wiki/Changes/Two_Week_Atomic
#
# Copyright (C) 2015 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0+
#
# Authors:
#     Adam Miller <maxamillion@fedoraproject.org>
#     Patrick Uiterwijk <puiterwijk@redhat.com>
#     Dusty Mabe <dusty@dustymabe.com>
#
# Exit codes:
#   0 - Success
#   1 - required arg missing
#   2 - no/partial information for given compose ID found
#   3 - subcommand failed, error message will be logged.
#   4 - execution canceled by user
#   5 - masher lock file found
#
#
# NOTE: This is bad and I feel bad for having written it, here there be dragons
# NOTE2: The atomic tree ref code is also ugly. Blame to Patrick, credits to Adam.

from __future__ import print_function
import os
import sys
import json
import glob
import shutil
import fnmatch
import smtplib
import argparse
import logging
import subprocess
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import fedfind.release

# Set log level to logging.INFO
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(os.path.basename(sys.argv[0]))

# Define "constants"
ATOMIC_REPO = "/mnt/koji/atomic/repo/"
ARCHES = ['x86_64', 'aarch64', 'ppc64le']

# Possible image types available for Atomic Host
IMAGE_TYPES = ['qcow2', 'raw-xz', 'vagrant-libvirt',
                 'vagrant-virtualbox', 'dvd-ostree']

# Mapping for image types to keep it consistent with twoweek fedmsg sent in past
IMAGE_TYPES_MAPPING = {
    'qcow2': 'atomic_qcow2',
    'raw-xz': 'atomic_raw',
    'vagrant-libvirt': 'atomic_vagrant_libvirt',
    'vagrant-virtualbox': 'atomic_vagrant_virtualbox',
    'dvd-ostree': 'atomic_dvd_ostree'
}

PREVIOUS_MAJOR_RELEASE_FINAL_COMMITS = {
    'aarch64': None,
    'ppc64le': None,
    'x86_64':  None,
}
TARGET_REF = "fedora/%s/%s/atomic-host" # example fedora/27/x86_64/atomic-host
COMPOSE_BASEDIR = "/mnt/koji/compose/twoweek/"

# FIXME ???? Do we need a real STMP server here?
ATOMIC_HOST_EMAIL_SMTP = "localhost"
ATOMIC_HOST_EMAIL_SENDER = "noreply@fedoraproject.org"

ATOMIC_HOST_FIRST_RELEASE_MAIL_RECIPIENTS = [
    "rel-eng@lists.fedoraproject.org",
]

ATOMIC_HOST_EMAIL_RECIPIENTS = [
    "devel@lists.fedoraproject.org",
    "cloud@lists.fedoraproject.org",
    "rel-eng@lists.fedoraproject.org",
    "atomic-devel@projectatomic.io",
    "atomic-announce@projectatomic.io",
]

# Full path will be:
#   /pub/alt/stage/$VERSION-$DATE/$IMAGE_TYPE/x86_64/[Images|os]/
# http://dl.fedoraproject.org/pub/alt/atomic/stable/
ATOMIC_HOST_STABLE_BASEDIR = "/pub/alt/atomic/stable/"

# the modname gets used to construct the fully qualified topic, like
# 'org.fedoraproject.prod.releng.blahblahblah'
ATOMIC_HOST_FEDMSG_MODNAME = "releng"
ATOMIC_HOST_FEDMSG_CERT_PREFIX = "releng"

DATAGREPPER_URL = "https://apps.fedoraproject.org/datagrepper/raw"
# delta = 2 weeks in seconds
DATAGREPPER_DELTA = 1209600
# category to filter on from datagrepper

# url: https://apps.fedoraproject.org/datagrepper/raw?topic=org.fedoraproject.prod.pungi.compose.ostree
DATAGREPPER_OSTREE_TOPIC = "org.fedoraproject.prod.pungi.compose.ostree"


SIGUL_SIGNED_TXT_PATH = "/tmp/signed"

# Number of atomic testing composes to keep around
ATOMIC_HOST_COMPOSE_PERSIST_LIMIT = 20


def get_ostree_compose_info(
        ostree_pungi_compose_id,
        datagrepper_url=DATAGREPPER_URL,
        delta=DATAGREPPER_DELTA,
        topic=DATAGREPPER_OSTREE_TOPIC):
    """
    get_ostree_compose_info

        Query datagrepper for fedmsg information from the compose.
        We'll find the ostree commits from this compose.

    return -> dict
        Will return arch->commit dictionariy

    """

    # rows_per_page is maximum 100 from Fedora's datagrepper
    request_params = {
        "delta": delta,
        "topic": 'org.fedoraproject.prod.pungi.compose.ostree',
        "rows_per_page": 100,
    }
    r = requests.get(datagrepper_url, params=request_params)

    # Start with page 1 response from datagrepper, grab the raw messages
    # and then continue to populate the list with the rest of the pages of data
    ostree_data = r.json()[u'raw_messages']
    for rpage in range(2, r.json()[u'pages']+1):
        ostree_data += requests.get(
            datagrepper_url,
            params=dict(page=rpage, **request_params)
        ).json()[u'raw_messages']

    ostree_composes = [
        compose[u'msg'] for compose in ostree_data
        if ostree_pungi_compose_id in compose[u'msg'][u'compose_id']
            and 'atomic-host' in compose[u'msg'][u'ref']
    ]

    ostree_compose_info = dict()
    for ostree_compose in ostree_composes:
        arch = ostree_compose[u'arch']
        commit = ostree_compose[u'commitid']
        ostree_compose_info[arch] = commit
        log.info("Found %s, %s", arch, commit)

    return ostree_compose_info

def get_release_artifacts_info_from_compose(pungi_compose_id):

    """
    :param pungi_compose_id: Pungi Compose ID considered for twoweek release
    :return: dict - Returns images detail for all supported arches for given
    compose ID.

    Image detail includes information like image url, image name,
    image size, Fedora release version and pungi compose ID in which image was
    built. Image can be of type qcow2, raw, iso and virtual box
    for which Fedora Atomic Host gets built against architectures. Currently we
    build for aarch64, ppc64le and x86_64 architectures.

    Example: dict structure is something like:
    {
        "aarch64": {
            "atomic_dvd_ostree": {
              "name": "Fedora-AtomicHost-ostree-aarch64-28-20180515.1.iso",
              "image_name": "Fedora-AtomicHost-ostree-aarch64-28-20180515.1.iso",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/aarch64/iso/Fedora-AtomicHost-ostree-aarch64-28-20180515.1.iso",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 988649472
            },
            "atomic_qcow2": {
              "name": "Fedora-AtomicHost-28-20180515.1",
              "image_name": "Fedora-AtomicHost-28-20180515.1.aarch64.qcow2",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/aarch64/images/Fedora-AtomicHost-28-20180515.1.aarch64.qcow2",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 621911040
            },
            "atomic_raw": {
              "name": "Fedora-AtomicHost-28-20180515.1",
              "image_name": "Fedora-AtomicHost-28-20180515.1.aarch64.raw.xz",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/aarch64/images/Fedora-AtomicHost-28-20180515.1.aarch64.raw.xz",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 396619232
            }
        },
        "x86_64": {
            ...
        },
        "ppc64le": {
            ...
        }
    }

    """

    # Use fedind to get image metadata information for given Pungi Compose ID
    # https://pagure.io/fedora-qa/fedfind
    log.info("Begin fetching image metadata information using fedfind for Compose ID %s", pungi_compose_id)
    compose_metadata = fedfind.release.get_release(cid=pungi_compose_id).metadata
    log.info("Finished fetching image metadata information using fedfind for Compose ID %s", pungi_compose_id)

    if not compose_metadata and not compose_metadata[u'composeinfo'] and not compose_metadata[u'images']:
        log.error("Image details not found for Compose ID : %s", pungi_compose_id)
        sys.exit(2)

    compose_id = compose_metadata[u'images'][u'payload'][u'compose'][u'id']
    release = compose_metadata[u'composeinfo'][u'payload'][u'release'][u'version']
    # Get Atomic Host related messages
    atomic_host_msg = compose_metadata[u'images'][u'payload'][u'images'][u'AtomicHost']
    release_artifacts_info = dict()

    for arch in ARCHES:
        if arch in atomic_host_msg:
            release_artifact_info = dict()
            images_detail = atomic_host_msg[arch]
            for image_detail in images_detail:
                if image_detail['type'] in IMAGE_TYPES:
                    image_url = os.path.join(ATOMIC_HOST_STABLE_BASEDIR,
                                             compose_id,
                                             image_detail[u'path'] )
                    image_name = image_detail[u'path'].split('/')[-1]
                    name = image_name.split('.' + arch)[0]
                    release_artifact_info[IMAGE_TYPES_MAPPING[image_detail[u'type']]] = {
                        "compose_id": compose_id,
                        "name": name,
                        "release": release,
                        "image_name": image_name,
                        "image_url": image_url,
                        "size": image_detail[u'size']
                    }
            if release_artifact_info:
                release_artifacts_info[arch] = release_artifact_info
        else:
            log.error("Image details not available for arch : %s", arch)
            sys.exit(2)

    return release_artifacts_info

def send_atomic_announce_email(
        email_filelist,
        ostree_commit_data,
        mail_receivers=ATOMIC_HOST_EMAIL_RECIPIENTS,
        sender_email=ATOMIC_HOST_EMAIL_SENDER,
        sender_smtp=ATOMIC_HOST_EMAIL_SMTP):
    """
    send_atomic_announce_email

        Send the atomic announce email to the desired recipients

    """

    released_artifacts = []
    released_checksums = []
    for e_file in email_filelist:
        if "CHECKSUM" in e_file:
            released_checksums.append(
                "https://alt.fedoraproject.org{}".format(e_file)
            )
        else:
            released_artifacts.append(
                "https://alt.fedoraproject.org{}".format(e_file)
            )
    released_artifacts.sort()
    released_checksums.sort()

    commits_string =""
    for arch in ARCHES:
        commit = ostree_commit_data[arch]['commit']
        commits_string += "Commit(%s): %s\n" % (arch, commit)

    msg = MIMEMultipart()
    msg['To'] = "; ".join(mail_receivers)
    msg['From'] = "noreply@fedoraproject.org"
    msg['Subject'] = "Fedora Atomic Host Two Week Release Announcement: %s" % \
                         ostree_commit_data.items()[0][1]['version']
    msg.attach(
        MIMEText(
            """
A new Fedora Atomic Host update is available via an OSTree update:

Version: {}
{}

We are releasing images from multiple architectures but please note
that x86_64 architecture is the only one that undergoes automated
testing at this time.

Existing systems can be upgraded in place via e.g. `atomic host upgrade`.

Corresponding image media for new installations can be downloaded from:

    https://getfedora.org/en/atomic/download/

Alternatively, image artifacts can be found at the following links:
{}

Respective signed CHECKSUM files can be found here:
{}

For direct download, the "latest" targets are always available here:
    https://getfedora.org/atomic_iso_latest
    https://getfedora.org/atomic_qcow2_latest
    https://getfedora.org/atomic_raw_latest
    https://getfedora.org/atomic_vagrant_libvirt_latest
    https://getfedora.org/atomic_vagrant_virtualbox_latest

Filename fetching URLs are available here:
    https://getfedora.org/atomic_iso_latest_filename
    https://getfedora.org/atomic_qcow2_latest_filename
    https://getfedora.org/atomic_raw_latest_filename
    https://getfedora.org/atomic_vagrant_libvirt_latest_filename
    https://getfedora.org/atomic_vagrant_virtualbox_latest_filename

For more information about the latest targets, please reference the Fedora
Atomic Wiki space.

    https://fedoraproject.org/wiki/Atomic_WG#Fedora_Atomic_Image_Download_Links

Do note that it can take some of the mirrors up to 12 hours to "check-in" at
their own discretion.

Thank you,
Fedora Release Engineering
            """.format(
                ostree_commit_data.items()[0][1]['version'],
                commits_string,
                '\n'.join(released_artifacts),
                '\n'.join(released_checksums)
            )
        )
    )

    # FIXME
    # Need to add package information to fill in the template email
    #
    #   The following changes are included in this update:

    try:
        s = smtplib.SMTP(sender_smtp)
        s.sendmail(sender_email, mail_receivers, msg.as_string())
    except smtplib.SMTPException as e:
        print("ERROR: Unable to send email:\n{}\n".format(e))

def stage_atomic_release(
        pungi_compose_id,
        compose_basedir=COMPOSE_BASEDIR,
        dest_base_dir=ATOMIC_HOST_STABLE_BASEDIR):
    """
    stage_atomic_release

        stage the release somewhere, this will remove the old and rsync up the
        new twoweek release

    """

    source_loc = os.path.join(compose_basedir, pungi_compose_id, "compose")
    dest_dir = os.path.join(dest_base_dir, pungi_compose_id)

    # FIXME - need sudo until pungi perms are fixed
    rsync_cmd = [
        'sudo',
        'rsync -avhHP --delete-after',
        '--exclude Cloud/',
        "{}/".format(source_loc),
        dest_dir
    ]
    # This looks silly but it gets everything properly split for
    # subprocess.call but keeps it from looking messy above.
    rsync_cmd = ' '.join(rsync_cmd).split()
    if subprocess.call(rsync_cmd):
        log.error(
            "stage_atomic_release: rsync command failed: {}".format(rsync_cmd)
        )
        exit(3)

def sign_checksum_files(
        key,
        artifact_path,
        signed_txt_path=SIGUL_SIGNED_TXT_PATH):
    """
    sign_checksum_files

        Use sigul to sign checksum files onces we know the successfully tested
        builds.
    """

    # Grab all the checksum_files
    checksum_files = []
    for full_dir_path, _, short_names in os.walk(artifact_path):
        for sname in fnmatch.filter(short_names, '*CHECKSUM'):
            checksum_files.append(
                os.path.join(
                    full_dir_path,
                    sname,
                )
            )

    for cfile in checksum_files:

        # Check to make sure this file isn't already signed, if it is then
        # don't sign it again
        already_signed = False
        with open(cfile, 'r') as f:
            for line in f.readlines():
                if "-----BEGIN PGP SIGNED MESSAGE-----" in line:
                    already_signed = True
                    break
        if already_signed:
            log.info(
                "sign_checksum_files: {} is already signed".format(cfile)
            )
            continue

        shutil.copy(cfile, signed_txt_path)

        # Basically all of this is ugly and I feel bad about it.
        sigulsign_cmd = [
            "sigul sign-text -o {} {} {}".format(
                signed_txt_path,
                key,
                cfile
            ),
        ]

        log.info("sign_checksum_files: Signing {}".format(cfile))
        # This looks silly but it gets everything properly split for
        # subprocess.call but keeps it from looking messy above.
        sigulsign_cmd = ' '.join(sigulsign_cmd).split()
        while subprocess.call(sigulsign_cmd):
            log.warn(
                "sigul command for {} failed, retrying".format(cfile)
            )

        if subprocess.call(
            "chgrp releng-team {}".format(signed_txt_path).split()
        ):
            log.error(
                "sign_checksum_files: chgrp releng-team {}".format(
                    signed_txt_path
                )
            )
            sys.exit(3)

        if subprocess.call(
            "chmod 664 {}".format(signed_txt_path).split()
        ):
            log.error(
                "sign_checksum_files: chmod 644 {}".format(
                    signed_txt_path
                )
            )
            sys.exit(3)

        # FIXME - need sudo until new pungi perms are sorted out
        if subprocess.call(
            #["sg", "releng-team", "'mv {} {}'".format(signed_txt_path, cfile)]
            "sudo mv {} {}".format(signed_txt_path, cfile).split()
        ):
            log.error(
                "sign_checksum_files: sudo sg releng-team 'mv {} {}' FAILED".format(
                    signed_txt_path,
                    cfile,
                )
            )
            sys.exit(3)


def fedmsg_publish(topic, msg):
    """ Try to publish a message on the fedmsg bus.

    But proceed happily if we weren't able to publish anything.
    """

    try:
        import fedmsg
        import fedmsg.config

        # Load config from disk with all the environment goodies.
        config = fedmsg.config.load_config()

        # And overwrite some values
        config['modname'] = ATOMIC_HOST_FEDMSG_MODNAME
        config['cert_prefix'] = ATOMIC_HOST_FEDMSG_CERT_PREFIX
        config['active'] = True

        # Send it.
        fedmsg.publish(topic=topic, msg=msg, **config)
    except Exception:
        # If you didn't know, log.exception automatically logs the traceback.
        log.exception("Failed to publish to fedmsg.")
        # But by passing, we don't let the exception bubble up and kill us.
        pass


def prune_old_composes(prune_base_dir, prune_limit):
    """
    prune_old_composes

        Clean up old testing composes from /pub/alt/

    :param prune_base_dir: str, path to base diretory needing pruning
    :param prune_limit: int, the number of composes that should be kept,
                        pruning all others.
    """

    prune_candidate_dirs = os.listdir(prune_base_dir)

    if len(prune_candidate_dirs) > 2:
        # Sort then reverse so we can slice the list from [0:prune_limit]
        prune_candidate_dirs.sort()
        prune_candidate_dirs.reverse()

        for candidate_dir in prune_candidate_dirs[0:prune_limit]:
            #try:
            #    shutil.rmtree(
            #        os.path.join(prune_base_dir, candidate_dir)
            #    )
            #except OSError, e:
            #    log.error(
            #        "Error trying to remove directory: {}\n{}".format(
            #            candidate_dir,
            #            e
            #        )
            #    )

            #FIXME - need to do this with sudo until pungi perms are fixed
            prune_cmd = "sudo rm -fr {}".format(
                os.path.join(
                    prune_base_dir,
                    candidate_dir
                )
            )
            if subprocess.call(prune_cmd.split()):
                log.error(
                    "prune_old_composes: command failed: {}".format(prune_cmd)
                )

def generate_static_delta(old_commit, new_commit):
    """
    generate_static_delta

        Generate a static delta between two commits

    :param old_commit - starting point for delta
    :param new_commit - ending point for delta
    """
    diff_cmd = ["/usr/bin/sudo",
                "ostree", "static-delta", "generate", "--repo",
                ATOMIC_REPO, "--if-not-exists",
                "--from", old_commit, "--to", new_commit]
    log.info("Creating Static Delta from %s to %s" % (old_commit, new_commit))
    if subprocess.call(diff_cmd):
        log.error("generate_static_delta: diff generation failed: %s", diff_cmd)
        exit(3)

def update_ostree_summary_file():
    """
    update_ostree_summary_file

        Update the summary file for the ostree repo

    """
    # Run as apache user because the files we are editing/creating
    # need to be owned by the apache user
    summary_cmd = ["/usr/bin/sudo", "ostree", "summary", "-u",
                   "--repo", ATOMIC_REPO]
    log.info("Updating Summary file")
    if subprocess.call(summary_cmd):
        log.error("update_ostree_summary_file: update failed: %s", summary_cmd)
        exit(3)

def update_ref(ref, old_commit, new_commit):
    """
    update_ref

        Update the given ref and set it to new_commit

    :param ref - the ref to update
    :param old_commit - where the ref currently is
    :param new_commit - where the ref should end up
    """

    if old_commit == new_commit:
        log.info("ref %s is already at %s. Skipping update",
                 ref, new_commit
        )
        return

    log.info("Moving ref %s from %s => %s",
              ref, old_commit, new_commit)

    reset_cmd = ['/usr/bin/sudo', 'ostree', 'reset', ref,
                 new_commit, '--repo', ATOMIC_REPO]
    if subprocess.call(reset_cmd):
        log.error("update_ref: resetting ref to new commit failed: %s", reset_cmd)
        sys.exit(3)




if __name__ == '__main__':

    # get args from command line
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-k",
        "--key",
        required=True,
        help="signing key to use with sigul",
    )
    parser.add_argument(
        "-r",
        "--release",
        required=True,
        help="Fedora Release to target for release (Ex: 24, 25, rawhide)",
    )
    parser.add_argument(
        "--pungi-compose-id",
        dest='pungi_compose_id',
        required=True,
        help="The pungi compose that created the media (Ex: Fedora-27-20171110.n.1)."
    )
    parser.add_argument(
        "--ostree-pungi-compose-id",
        dest='ostree_pungi_compose_id',
        help="""
           The pungi compose that created the ostree (Ex: Fedora-27-20171110.n.1).
           This is optional and is only required if the pungi compose that ostree
           commit is different than the ostree compose that created the media.
        """
    )
    parser.add_argument(
        "--first-release",
        dest='first_release',
        action='store_true',
        default=False,
        help="""
           Indicates that this is the first release for this stream and email
           audience should be limited and we don't need to worry about creating
           an incremental static delta.
        """
    )
    pargs = parser.parse_args()

    # This one is only specified if it differs from --pungi-compose-id
    # If missing just assign it the value of pungi-compose-id.
    if not pargs.ostree_pungi_compose_id:
        pargs.ostree_pungi_compose_id = pargs.pungi_compose_id

    log.info("Fetching images information for Compose ID %s", pargs.pungi_compose_id )
    # Get image artifacts information for given Pungi Compose ID
    release_artifacts_info = get_release_artifacts_info_from_compose(
                                pargs.pungi_compose_id)
    log.info("{}\n{}".format("RELEASE_ARTIFACTS_INFO", json.dumps(release_artifacts_info, indent=2)))

    log.info("Fetching images information from compose ID %s complete", pargs.pungi_compose_id)
    # If the dict is empty, artifacts information not found for given compose ID
    if not release_artifacts_info:
        log.error("Images information not found for Compose ID %s", pargs.pungi_compose_id)
        sys.exit(2)

    # Initialize a empty dict that we will populate with information
    # about each commit. We'll use this information to do the release.
    # Example: => {
    #   'x86_64' => {
    #       'ref'    => 'fedora/27/x86_64/atomic-host',
    #       'commit' => 'xxyyzz',
    #       'version' => '27.1'
    #       'previous_commit' => 'aabbccdd'
    #   }
    # }
    ostree_commit_data = dict()
    for arch in ARCHES:
        ostree_commit_data[arch] = dict()

    # Get commit information from fedmsg for the specified ostree
    # compose. This will give us back a dict of arch->commit.
    ostree_compose_info = get_ostree_compose_info(pargs.ostree_pungi_compose_id)

    # Verify there is a commit for each of the architectures.
    for arch in ARCHES:
        if arch not in ostree_compose_info.keys():
            log.error("No compose commit info for %s in %s",
                        arch, pargs.ostree_pungi_compose_id)
            sys.exit(2)

    # populate the ostree_commit_data dict
    for arch in ARCHES:
        commit = ostree_compose_info[arch]
        ref = TARGET_REF % (pargs.release, arch)

        # Verify the commit exists in the tree, and find the version
        log.info("Verifying and finding version of %s", commit)
        cmd = ['/usr/bin/ostree', '--repo=' + ATOMIC_REPO,
               'show', '--print-metadata-key=version', commit]
        version = subprocess.check_output(cmd).strip()
        # output will be in GVariant print format by default -> s/'//
        version = version.replace("'", "")

        # Find the previous commit for this ref in the tree
        cmd = ['/usr/bin/ostree', '--repo=' + ATOMIC_REPO,
               'rev-parse', ref]
        previous_commit = subprocess.check_output(cmd).strip()

        # set info in ostree_commit_data dict
        ostree_commit_data[arch]['ref'] = ref
        ostree_commit_data[arch]['commit'] = commit
        ostree_commit_data[arch]['version'] = version
        ostree_commit_data[arch]['previous_commit'] = previous_commit

    log.info("OSTREE COMMIT DATA INFORMATION")
    log.info("%s", json.dumps(ostree_commit_data, indent=2))

    # Verify all versions match
    ostree_commit_version = ostree_commit_data.items()[0][1]['version']
    for arch in ARCHES:
        if ostree_commit_data[arch]['version'] != ostree_commit_version:
            log.error("Found mismatched versions for commits")
            log.error("Got %s for %s. Expected %s",
                      ostree_commit_data[arch]['version'],
                      ostree_commit_data[arch]['commit'],
                      ostree_commit_version)
            sys.exit(1)

    log.info("Releasing ostrees at version: %s", ostree_commit_version)

    # url: https://apps.fedoraproject.org/datagrepper/raw?topic=org.fedoraproject.prod.releng.atomic.twoweek.begin
    log.info("Sending fedmsg releng.atomic.twoweek.begin")
    fedmsg_publish(
        topic="atomic.twoweek.begin",
        msg=dict(**release_artifacts_info)
    )

    log.info("Signing image metadata - compose")
    sign_checksum_files(
        pargs.key,
        os.path.join(COMPOSE_BASEDIR, pargs.pungi_compose_id),
    )

    # Perform the necessary ostree repo manipulations for the release
    # for each arch:
    #     - create static delta from previous release
    #     - create static delta from previous major release
    #     - update the ref in the repo to the new commit
    for arch in ARCHES:
        # Generate static delta from previous release (if not 1st release)
        if not pargs.first_release:
            generate_static_delta(
                old_commit=ostree_commit_data[arch]['previous_commit'],
                new_commit=ostree_commit_data[arch]['commit']
            )

        # Generate static delta from previous major release (if defined)
        old_commit = PREVIOUS_MAJOR_RELEASE_FINAL_COMMITS.get(arch, None)
        if old_commit is not None:
            generate_static_delta(
                old_commit=old_commit,
                new_commit=ostree_commit_data[arch]['commit'],
            )
        # Move the ref
        update_ref(
            ostree_commit_data[arch]['ref'],
            ostree_commit_data[arch]['previous_commit'],
            ostree_commit_data[arch]['commit']
        )
        # Update summary file
        update_ostree_summary_file()

    log.info("Staging release content in /pub/alt/atomic/stable/")
    stage_atomic_release(pargs.pungi_compose_id)

    # url: https://apps.fedoraproject.org/datagrepper/raw?topic=org.fedoraproject.prod.releng.atomic.twoweek.complete
    log.info("Sending fedmsg releng.atomic.twoweek.complete")
    fedmsg_publish(
        topic="atomic.twoweek.complete",
        msg=dict(**release_artifacts_info)
    )

    log.info("Sending Two Week Atomic Host announcement email")
    # Find all the Atomic Host images and CHECKSUM files to include in the email
    email_filelist = []
    for full_dir_path, _, short_names in \
            os.walk(os.path.join(ATOMIC_HOST_STABLE_BASEDIR,
                                 pargs.pungi_compose_id)):
        for sname in fnmatch.filter(short_names, '*Atomic*'):
            email_filelist.append(
                os.path.join(
                    full_dir_path,
                    sname,
                )
            )
            for c_file in glob.glob(os.path.join(full_dir_path, "*CHECKSUM")):
                email_filelist.append(c_file)

    # On the first release send only to "FIRST_RELEASE" list
    if pargs.first_release:
        mail_receivers = ATOMIC_HOST_FIRST_RELEASE_MAIL_RECIPIENTS
    else: 
        mail_receivers = ATOMIC_HOST_EMAIL_RECIPIENTS
    send_atomic_announce_email(set(email_filelist),
                               ostree_commit_data,
                               mail_receivers=mail_receivers)

    # FIXME - The logic in this function is broken, leave it disabled for now
    #log.info("Pruning old Atomic Host test composes")
    #prune_old_composes(ATOMIC_HOST_STABLE_BASEDIR, 2)

    log.info("Two Week Atomic Host Release Complete!")

    print("############REMINDER##########\n#\n#\n")
    print("Reset the block-release value to false in {}".format(
        "https://pagure.io/mark-atomic-bad"
    ))

# vim: set expandtab sw=4 sts=4 ts=4
