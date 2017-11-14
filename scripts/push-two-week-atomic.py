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
#
# Exit codes:
#   0 - Success
#   1 - required arg missing
#   2 - no successful AutoCloud builds found
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

# Set log level to logging.INFO
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(os.path.basename(sys.argv[0]))

# Define "constants"
ATOMIC_HOST_DIR = "/mnt/koji/compose/updates/atomic"
ARCHES = ['x86_64', 'aarch64', 'ppc64le']
PREVIOUS_MAJOR_RELEASE_FINAL_COMMITS = {
    'aarch64': None,
    'ppc64le': None,
    'x86_64':  'c099633883cd8d06895e32a14c63f6672072430c151de882223e4abe20efa7ca',
}
TARGET_REF = "fedora/%s/%s/atomic-host" # example fedora/27/x86_64/atomic-host
COMPOSE_BASEDIR = "/mnt/koji/compose/twoweek/"

# FIXME ???? Do we need a real STMP server here?
ATOMIC_HOST_EMAIL_SMTP = "localhost"
ATOMIC_HOST_EMAIL_SENDER = "noreply@fedoraproject.org"

ATOMIC_HOST_EMAIL_RECIPIENTS = [
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

MARK_ATOMIC_HOST_BAD_COMPOSES = None
MARK_ATOMIC_HOST_GOOD_COMPOSES = None
BLOCK_ATOMIC_HOST_RELEASE = None

try:
    MARK_ATOMIC_HOST_BAD_JSON_URL = \
        'https://pagure.io/mark-atomic-bad/raw/master/f/bad-composes.json'
    MARK_ATOMIC_HOST_BAD_JSON = requests.get(MARK_ATOMIC_HOST_BAD_JSON_URL).text
    MARK_ATOMIC_HOST_BAD_COMPOSES = json.loads(MARK_ATOMIC_HOST_BAD_JSON)[u'bad-composes']

    BLOCK_ATOMIC_HOST_RELEASE_JSON_URL = \
        'https://pagure.io/mark-atomic-bad/raw/master/f/block-release.json'
    BLOCK_ATOMIC_HOST_RELEASE_JSON = \
        requests.get(BLOCK_ATOMIC_HOST_RELEASE_JSON_URL).text
    BLOCK_ATOMIC_HOST_RELEASE = \
        json.loads(BLOCK_ATOMIC_HOST_RELEASE_JSON)[u'block-release']

    MARK_ATOMIC_HOST_GOOD_URL = \
        'https://pagure.io/mark-atomic-bad/raw/master/f/good-composes.json'
    MARK_ATOMIC_HOST_GOOD_JSON = \
        requests.get(MARK_ATOMIC_HOST_GOOD_URL).text
    MARK_ATOMIC_HOST_GOOD_COMPOSES = \
        json.loads(MARK_ATOMIC_HOST_GOOD_JSON)[u'good-composes']
except Exception as e:
    log.exception(
        "!!!!{0}!!!!\n{1}".format("Failed to fetch or parse json", e)
    )
    sys.exit(1)


DATAGREPPER_URL = "https://apps.fedoraproject.org/datagrepper/raw"
# delta = 2 weeks in seconds
DATAGREPPER_DELTA = 1209600
# category to filter on from datagrepper
# url: https://apps.fedoraproject.org/datagrepper/raw?topic=org.fedoraproject.prod.autocloud.compose.complete
DATAGREPPER_AUTOCLOUD_TOPIC = "org.fedoraproject.prod.autocloud.compose.complete"
# url: https://apps.fedoraproject.org/datagrepper/raw?topic=org.fedoraproject.prod.pungi.compose.ostree
DATAGREPPER_OSTREE_TOPIC = "org.fedoraproject.prod.pungi.compose.ostree"


SIGUL_SIGNED_TXT_PATH = "/tmp/signed"

# Number of atomic testing composes to keep around
ATOMIC_HOST_COMPOSE_PERSIST_LIMIT = 20


def construct_url(msg):
    """ Construct the final URL from koji URL.

    Takes an autocloud fedmsg message and returns the image name and final url.
    """
    iul = msg[u'image_url'].split('/')

    # This isn't used in the path for the destination dir, it's in there twice
    iul.remove('compose')
    iul.remove('compose')

    image_name = iul[-1]
    image_url = os.path.join(ATOMIC_HOST_STABLE_BASEDIR, '/'.join(iul[4:]))
    return image_name, image_url

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
    autocloud_data = r.json()[u'raw_messages']
    for rpage in range(2, r.json()[u'pages']+1):
        autocloud_data += requests.get(
            datagrepper_url,
            params=dict(page=rpage, **request_params)
        ).json()[u'raw_messages']

    ostree_composes = [
        compose[u'msg'] for compose in autocloud_data
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

def get_latest_successful_autocloud_test_info(
        release,
        pungi_compose_id,
        datagrepper_url=DATAGREPPER_URL,
        delta=DATAGREPPER_DELTA,
        topic=DATAGREPPER_AUTOCLOUD_TOPIC):
    """
    get_latest_successful_autocloud_test_info

        Query datagrepper[0] to find the latest successful Atomic Host images via
        the autocloud[1] tests.

    return -> dict
        Will return the build information of the latest successful build

    [0] - https://apps.fedoraproject.org/datagrepper/
    [1] - https://github.com/kushaldas/autocloud/
    """

    # rows_per_page is maximum 100 from Fedora's datagrepper
    request_params = {
        "delta": delta,
        "topic": topic,
        "rows_per_page": 100,
    }
    r = requests.get(datagrepper_url, params=request_params)

    # Start with page 1 response from datagrepper, grab the raw messages
    # and then continue to populate the list with the rest of the pages of data
    autocloud_data = r.json()[u'raw_messages']
    for rpage in range(2, r.json()[u'pages']+1):
        autocloud_data += requests.get(
            datagrepper_url,
            params=dict(page=rpage, **request_params)
        ).json()[u'raw_messages']


# XXX ignore this way of doing things for now (see below)
##### List comprehension that will return a list of compose information from
##### AutoCloud (the [u'msg'] payload of autocloud.compose.complete fedmsg)
##### such that the following criteria are true:
#####
#####   - Is an Atomic Host compose (i.e. 'Atomic' is in the compose id)
#####   - No compose artifacts failed the tests
#####   - This is the current Fedora release we want
#####
#####   OR:
#####       - This compose was manually marked good
####candidate_composes = [
####    compose[u'msg'] for compose in autocloud_data
####        if u'Atomic' in compose[u'msg'][u'id']
####            and compose[u'msg'][u'results'][u'failed'] == 0
####            and compose[u'msg'][u'release'] == str(release)
####            or compose[u'msg'][u'id'] in MARK_ATOMIC_HOST_GOOD_COMPOSES
####]

####filtered_composes = list(candidate_composes)
####for compose in candidate_composes:
####    if compose_manually_marked_bad(compose[u'id']):
####        filtered_composes.remove(compose)

##### sc = successful compose
####sc = filtered_composes[0]

    # XXX For now ignore the autocloud results and just use the
    # requested pungi compose id.
    #
    # List comprehension that will return a list of compose information from
    # AutoCloud (the [u'msg'] payload of autocloud.compose.complete fedmsg)
    # such that the following criteria are true:
    candidate_composes = [
        compose[u'msg'] for compose in autocloud_data
            if pungi_compose_id in compose[u'msg'][u'id']
    ]
    # sc = successful compose
    sc = candidate_composes[0]

    autocloud_info = {}

    # qcow2 image
    qcow_msg = [
        sc[u'results'][u'artifacts'][img] for img in sc[u'results'][u'artifacts']
            if sc[u'results'][u'artifacts'][img][u'family'] == u'Atomic'
            and sc[u'results'][u'artifacts'][img][u'type'] == u'qcow2'
    ][0]
    image_name, image_url = construct_url(qcow_msg)
    autocloud_info["atomic_qcow2"] = {
        "compose_id": sc[u'id'],
        "name": qcow_msg[u'name'],
        "release": sc[u'release'],
        "image_name": image_name,
        "image_url": image_url,
    }

    # raw image
    #
    # FIXME - This is a bit of a hack right now, but the raw image is what
    #         the qcow2 is made of so only qcow2 is tested and infers the
    #         success of both qcow2 and raw.xz
    autocloud_info["atomic_raw"] = {
        "compose_id": sc[u'id'],
        "name": qcow_msg[u'name'],
        "release": sc[u'release'],
        "image_name": image_name.replace('qcow2', 'raw.xz'),    # HACK
        "image_url": image_url.replace('qcow2', 'raw.xz'),      # HACK
    }

    # vagrant libvirt image
    vlibvirt_msg = [
        sc[u'results'][u'artifacts'][img] for img in sc[u'results'][u'artifacts']
            if sc[u'results'][u'artifacts'][img][u'family'] == u'Atomic'
            and sc[u'results'][u'artifacts'][img][u'type'] == u'vagrant-libvirt'
    ][0]
    image_name, image_url = construct_url(vlibvirt_msg)
    autocloud_info["atomic_vagrant_libvirt"] = {
        "compose_id": sc[u'id'],
        "name": vlibvirt_msg[u'name'],
        "release": sc[u'release'],
        "image_name": image_name,
        "image_url": image_url,
    }

    # vagrant vbox image
    vvbox_msg = [
        sc[u'results'][u'artifacts'][img] for img in sc[u'results'][u'artifacts']
            if sc[u'results'][u'artifacts'][img][u'family'] == u'Atomic'
            and sc[u'results'][u'artifacts'][img][u'type'] == u'vagrant-virtualbox'
    ][0]
    image_name, image_url = construct_url(vvbox_msg)
    autocloud_info["atomic_vagrant_virtualbox"] = {
        "compose_id": sc[u'id'],
        "name": vvbox_msg[u'name'],
        "release": sc[u'release'],
        "image_name": image_name,
        "image_url": image_url,
    }

    return autocloud_info


def compose_manually_marked_bad(compose_id, bad_composes=MARK_ATOMIC_HOST_BAD_COMPOSES):
    """
    compose_manually_marked_bad

        Check for a compose that has been marked bad manually

        compose_id
            Compose id of most recently found auto-tested good compose build

    return -> bool
        True if the build was marked bad, else False
    """

    bad = [c for c in bad_composes if c == compose_id]

    return len(bad) > 0

def send_atomic_announce_email(
        email_filelist,
        mail_receivers=ATOMIC_HOST_EMAIL_RECIPIENTS,
        sender_email=ATOMIC_HOST_EMAIL_SENDER,
        sender_smtp=ATOMIC_HOST_EMAIL_SMTP,
        tree_commit=None,
        tree_version=None):
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

    msg = MIMEMultipart()
    msg['To'] = "; ".join(mail_receivers)
    msg['From'] = "noreply@fedoraproject.org"
    msg['Subject'] = "Fedora Atomic Host Two Week Release Announcement"
    msg.attach(
        MIMEText(
            """
A new Fedora Atomic Host update is available via an OSTree commit:

Commit: {}
Version: {}

Existing systems can be upgraded in place via e.g. `atomic host upgrade` or
`atomic host deploy`.

Corresponding image media for new installations can be downloaded from:

    https://getfedora.org/en/atomic/download/

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
Cloud Wiki space.

    https://fedoraproject.org/wiki/Cloud#Quick_Links

Do note that it can take some of the mirrors up to 12 hours to "check-in" at
their own discretion.

Thank you,
Fedora Release Engineering
            """.format(
                tree_commit,
                tree_version,
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
                ATOMIC_HOST_DIR, "--if-not-exists", "--from", old_commit,
                "--to", new_commit]
    log.info("Creating Static Delta from %s to %s" % (old_commit, new_commit))
    if subprocess.call(diff_cmd):
        log.error("generate_static_delta: diff generation failed: %s", diff_cmd)
        exit(3)

def update_ref(ref, old_commit, new_commit):
    """
    update_ref

        Update the given ref and set it to new_commit

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
                 new_commit, '--repo', ATOMIC_HOST_DIR]
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
    pargs = parser.parse_args()

    # This one is only specified if it differs from --pungi-compose-id
    # If missing just assign it the value of pungi-compose-id.
    if not pargs.ostree_pungi_compose_id:
        pargs.ostree_pungi_compose_id = pargs.pungi_compose_id

    log.info("Checking to make sure release is not currently blocked")
    if BLOCK_ATOMIC_HOST_RELEASE:
        log.info("Release Blocked: Exiting.")
        sys.exit(0)

    log.info("Querying datagrepper for latest AutoCloud successful tests")
    # Acquire the latest successful builds from datagrepper
    tested_autocloud_info = get_latest_successful_autocloud_test_info(
        pargs.release, pargs.pungi_compose_id
    )
    log.info("{}\n{}".format("TESTED_AUTOCLOUD_INFO", json.dumps(tested_autocloud_info, indent=2)))

    log.info("Query to datagrepper complete")
    # If the dict is empty, there were no successful builds in the last two
    # weeks, error accordingly
    if not tested_autocloud_info:
        log.error("No successful builds found")
        sys.exit(2)

   ## XXX Not needed since we are specifying compose ID
   #log.info("Extracting compose_id from tested autocloud data")
   #compose_id = tested_autocloud_info['atomic_qcow2']['compose_id']
   #
   ## TODO: https://github.com/kushaldas/tunirtests/pull/59 will allow us to
   ## extract this from the autocloud test results.
   #print('Releasing compose %s' % compose_id)

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
        cmd = ['/usr/bin/ostree', '--repo=' + ATOMIC_HOST_DIR,
               'show', '--print-metadata-key=version', commit]
        version = subprocess.check_output(cmd).strip()
        # output will be in GVariant print format by default -> s/'//
        version = version.replace("'", "")

        # Find the previous commit for this ref in the tree
        cmd = ['/usr/bin/ostree', '--repo=' + ATOMIC_HOST_DIR,
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
        msg=dict(**tested_autocloud_info)
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
        # Generate static delta from previous release
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
            ostree_commit_data[arch]['commit']
        )

    log.info("Staging release content in /pub/alt/atomic/stable/")
    stage_atomic_release(pargs.pungi_compose_id)

    # url: https://apps.fedoraproject.org/datagrepper/raw?topic=org.fedoraproject.prod.releng.atomic.twoweek.complete
    log.info("Sending fedmsg releng.atomic.twoweek.complete")
    fedmsg_publish(
        topic="atomic.twoweek.complete",
        msg=dict(**tested_autocloud_info)
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

    send_atomic_announce_email(set(email_filelist), tree_commit=tree_commit,
                               tree_version=tree_version)

    # FIXME - The logic in this functioni is broken, leave it disabled for now
    #log.info("Pruning old Atomic Host test composes")
    #prune_old_composes(ATOMIC_HOST_STABLE_BASEDIR, 2)

    log.info("Two Week Atomic Host Release Complete!")

    print("############REMINDER##########\n#\n#\n")
    print("Reset the block-release value to false in {}".format(
        "https://pagure.io/mark-atomic-bad"
    ))

# vim: set expandtab sw=4 sts=4 ts=4
