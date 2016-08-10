#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# push-two-week-atomic.py - An utility to sync two-week Atomic releases
#
# For more information about two-week Atomic releases please visit:
#   https://fedoraproject.org/wiki/Changes/Two_Week_Atomic
#
# Copyright (C) 2015 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0+
#
# Authors:
#     Adam Miller <maxamillion@fedoraproject.org>
#
# Exit codes:
#   0 - Success
#   1 - required arg missing
#   2 - no successful AutoCloud builds found
#   3 - subcommand failed, error message will be logged.
#
#
# NOTE: This is bad and I feel bad for having written it, here there be dragons

import os
import sys
import json
import glob
import time
import shutil
import fnmatch
import smtplib
import argparse
import logging
import datetime
import subprocess

import requests

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Set log level to logging.INFO
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(os.path.basename(sys.argv[0]))

# Define "constants"
COMPOSE_BASEDIR = "/mnt/koji/compose/twoweek/"

# FIXME ???? Do we need a real STMP server here?
ATOMIC_EMAIL_SMTP = "localhost"
ATOMIC_EMAIL_SENDER = "noreply@fedoraproject.org"

ATOMIC_EMAIL_RECIPIENTS = [
    "cloud@lists.fedoraproject.org",
    "rel-eng@lists.fedoraproject.org",
    "atomic-devel@projectatomic.io",
    "atomic-announce@projectatomic.io",
]

# Full path will be:
#   /pub/alt/stage/$VERSION-$DATE/$IMAGE_TYPE/x86_64/[Images|os]/
# http://dl.fedoraproject.org/pub/alt/atomic/stable/
ATOMIC_TESTING_BASEDIR = "/pub/alt/atomic/testing/"
ATOMIC_STABLE_DESTINATION = "/pub/alt/atomic/stable/"

# the modname gets used to construct the fully qualified topic, like
# 'org.fedoraproject.prod.releng.blahblahblah'
ATOMIC_FEDMSG_MODNAME = "releng"
ATOMIC_FEDMSG_CERT_PREFIX = "releng"

MARK_ATOMIC_BAD_COMPOSES = None
MARK_ATOMIC_GOOD_COMPOSES = None
BLOCK_ATOMIC_RELEASE = None

try:
    MARK_ATOMIC_BAD_JSON_URL = \
        'https://pagure.io/mark-atomic-bad/raw/master/f/bad-composes.json'
    MARK_ATOMIC_BAD_JSON = requests.get(MARK_ATOMIC_BAD_JSON_URL).text
    MARK_ATOMIC_BAD_COMPOSES = json.loads(MARK_ATOMIC_BAD_JSON)[u'bad-composes']

    BLOCK_ATOMIC_RELEASE_JSON_URL = \
        'https://pagure.io/mark-atomic-bad/raw/master/f/block-release.json'
    BLOCK_ATOMIC_RELEASE_JSON = \
        requests.get(BLOCK_ATOMIC_RELEASE_JSON_URL).text
    BLOCK_ATOMIC_RELEASE = \
        json.loads(BLOCK_ATOMIC_RELEASE_JSON)[u'block-release']

    MARK_ATOMIC_GOOD_URL = \
        'https://pagure.io/mark-atomic-bad/raw/master/f/good-composes.json'
    MARK_ATOMIC_GOOD_JSON = \
        requests.get(MARK_ATOMIC_GOOD_URL).text
    MARK_ATOMIC_GOOD_COMPOSES = \
        json.loads(MARK_ATOMIC_GOOD_JSON)[u'good-composes']
except Exception, e:
    log.exception(
        "!!!!{0}!!!!\n{0}".format("Failed to fetch or parse json", e)
    )
    sys.exit(1)


DATAGREPPER_URL = "https://apps.fedoraproject.org/datagrepper/raw"
# delta = 2 weeks in seconds
DATAGREPPER_DELTA = 1209600
# category to filter on from datagrepper
DATAGREPPER_TOPIC = "org.fedoraproject.prod.autocloud.image.success"


SIGUL_SIGNED_TXT_PATH = "/tmp/signed"

# Number of atomic testing composes to keep around
ATOMIC_COMPOSE_PERSIST_LIMIT = 20


def construct_url(msg):
    """ Construct the final URL from koji URL.

    Takes an autocloud fedmsg message and returns the image name and final url.
    """
    dest_dir = ATOMIC_STABLE_DESTINATION + 'CloudImages/x86_64/images/'
    image_name = msg[u'msg'][u'compose_url'].split('/')[-1]
    image_url = dest_dir + image_name
    return image_name, image_url


def get_latest_successful_autocloud_test_info(
        release,
        datagrepper_url=DATAGREPPER_URL,
        delta=DATAGREPPER_DELTA,
        topic=DATAGREPPER_TOPIC):
    """
    get_latest_successful_autocloud_test_info

        Query datagrepper[0] to find the latest successful Atomic images via
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

    # FIXME - I would like to find a good way to extract the types from the
    #         datagrepper query instead of specifying each artifact
    atomic_qcow2 = [
        s for s in autocloud_data
        if s[u'msg'][u'status'] == u'success'
        and fnmatch.fnmatch(s[u'msg'][u'image_name'], u'Fedora-Atomic-*')
        and s[u'msg'][u'type'] == u"qcow2"
        and not compose_manually_marked_bad(s[u'msg'][u'compose_id'])
    ]

    atomic_vagrant_libvirt = [
        s for s in autocloud_data
        if s[u'msg'][u'status'] == u'success'
        and fnmatch.fnmatch(s[u'msg'][u'image_name'], u'Fedora-Atomic-*')
        and s[u'msg'][u'type'] == u"vagrant-libvirt"
        and not compose_manually_marked_bad(s[u'msg'][u'compose_id'])
    ]

    atomic_vagrant_vbox = [
        s for s in autocloud_data
        if s[u'msg'][u'status'] == u'success'
        and fnmatch.fnmatch(s[u'msg'][u'image_name'], u'Fedora-Atomic-*')
        and s[u'msg'][u'type'] == u"vagrant-virtualbox"
        and not compose_manually_marked_bad(s[u'msg'][u'compose_id'])
    ]

    # HACK
    #
    # Handle manually marked "good" builds that were false positives in
    # AutoCloud
    if MARK_ATOMIC_GOOD_COMPOSES:
        release_cycle_time = time.time() - DATAGREPPER_DELTA
        atomic_qcow2_failed = [
            s for s in autocloud_data
            if s[u'msg'][u'status'] == u'failed'
            and fnmatch.fnmatch(s[u'msg'][u'image_name'], u'Fedora-Atomic-*')
            and s[u'msg'][u'type'] == u"qcow2"
            and not compose_manually_marked_bad(s[u'msg'][u'compose_id'])
        ]

        atomic_vagrant_libvirt_failed = [
            s for s in autocloud_data
            if s[u'msg'][u'status'] == u'failed'
            and fnmatch.fnmatch(s[u'msg'][u'image_name'], u'Fedora-Atomic-*')
            and s[u'msg'][u'type'] == u"vagrant-libvirt"
            and not compose_manually_marked_bad(s[u'msg'][u'compose_id'])
        ]

        atomic_vagrant_vbox_failed = [
            s for s in autocloud_data
            if s[u'msg'][u'status'] == u'failed'
            and fnmatch.fnmatch(s[u'msg'][u'image_name'], u'Fedora-Atomic-*')
            and s[u'msg'][u'type'] == u"vagrant-virtualbox"
            and not compose_manually_marked_bad(s[u'msg'][u'compose_id'])
        ]

        # Define some helpers to deal with some of this badness
        # Thanks to Ralph(threebean) for the suggestion/patch to try and
        # bring sanity to chaos
        url2image = lambda s: s.split('/')[-1]
        image2release = lambda s: int(s.split('.')[0].split('-')[-1])

        for good_compose in MARK_ATOMIC_GOOD_COMPOSES:
            good_compose_date = str(image2release(good_compose))
            release_window = datetime.datetime.strptime(good_compose_date, "%Y%m%d")

            if time.mktime(release_window.timetuple()) > release_cycle_time:

                # NOTE: By appending, we won't override an "organically"
                #       passed test from AutoCloud because the selector
                #       below gets index 0 of the different atomic_ lists
                #
                #       We then insert at index 0 when the manually entered
                #       successful build is newer than the latest
                #       "organically" passed test

                # check against atomic_qcow2
                for check_build in atomic_qcow2_failed:
                    if good_compose == url2image(check_build[u'msg'][u'compose_id']):
                        if len(atomic_qcow2) > 0:
                            candidate = url2image(atomic_qcow2[0][u'msg'][u'compose_url'])
                            if image2release(candidate) < image2release(good_compose):
                                atomic_qcow2.insert(0, check_build)
                            else:
                                atomic_qcow2.append(check_build)
                        else:
                            atomic_qcow2.append(check_build)

                # check against vagrant_libvirt
                for check_build in atomic_vagrant_libvirt_failed:
                    if good_compose == url2image(check_build[u'msg'][u'compose_url']):
                        if len(atomic_vagrant_libvirt) > 0:
                            candidate = url2image(atomic_vagrant_libvirt[0][u'msg'][u'compose_url'])
                            if image2release(candidate) < image2release(good_compose):
                                atomic_vagrant_libvirt.insert(0, check_build)
                            else:
                                atomic_vagrant_libvirt.append(check_build)
                        else:
                            atomic_vagrant_libvirt.append(check_build)

                # check against vagrant_vbox
                for check_build in atomic_vagrant_vbox_failed:
                    if good_compose == url2image(check_build[u'msg'][u'compose_url']):
                        if len(atomic_vagrant_vbox) > 0:
                            candidate = url2image(atomic_vagrant_vbox[0][u'msg'][u'compose_url'])
                            if image2release(candidate) < image2release(good_compose):
                                atomic_vagrant_vbox.insert(0, check_build)
                            else:
                                atomic_vagrant_vbox.append(check_build)
                        else:
                            atomic_vagrant_vbox.append(check_build)

    autocloud_info = {}

    # Yet another hack because AutoCloud still doesn't give us this information
    # even though the rewrite was supposed to
    extract_compose_id = lambda x: x[u'msg']['compose_id']
    qcow2_composes = map(extract_compose_id, atomic_qcow2)
    vagrant_libvirt_composes = map(extract_compose_id, atomic_vagrant_libvirt)
    vagrant_vbox_composes = map(extract_compose_id, atomic_vagrant_vbox)
    compose = [c for c in qcow2_composes
               if c in vagrant_vbox_composes
               and c in vagrant_libvirt_composes][0]

    # sc = successful compose because we've now coorelated the data to a single
    #       compose that's successful across all images
    sc_qcow2 = [i for i in atomic_qcow2 if i[u'msg'][u'compose_id'] == compose]
    sc_vagrant_libvirt = [i for i in atomic_vagrant_libvirt if i[u'msg'][u'compose_id'] == compose]
    sc_vagrant_vbox = [i for i in atomic_vagrant_vbox if i[u'msg'][u'compose_id'] == compose]


    if sc_qcow2:
        image_name, image_url = construct_url(sc_qcow2[0])
        autocloud_info["atomic_qcow2"] = {
            "compose_id": sc_qcow2[0][u'msg'][u'compose_id'],
            "name": sc_qcow2[0][u'msg'][u'image_name'],
            "release": sc_qcow2[0][u'msg'][u'release'],
            "image_name": image_name,
            "image_url": image_url,
        }

        # FIXME - This is a bit of a hack right now, but the raw image is what
        #         the qcow2 is made of so only qcow2 is tested and infers the
        #         success of both qcow2 and raw.xz
        autocloud_info["atomic_raw"] = {
            "compose_id": sc_qcow2[0][u'msg'][u'compose_id'],
            "name": sc_qcow2[0][u'msg'][u'image_name'] + '-Raw',
            "release": sc_qcow2[0][u'msg'][u'release'],
            "image_name": image_name.replace('qcow2', 'raw.xz'),    # HACK
            "image_url": image_url.replace('qcow2', 'raw.xz'),      # HACK
        }

    if sc_vagrant_libvirt:
        image_name, image_url = construct_url(atomic_vagrant_libvirt[0])
        autocloud_info["atomic_vagrant_libvirt"] = {
            "compose_id": sc_vagrant_libvirt[0][u'msg'][u'compose_id'],
            "name": sc_vagrant_libvirt[0][u'msg'][u'image_name'],
            "release": sc_vagrant_libvirt[0][u'msg'][u'release'],
            "image_name": image_name,
            "image_url": image_url,
        }

    if sc_vagrant_vbox:
        image_name, image_url = construct_url(atomic_vagrant_vbox[0])
        autocloud_info["atomic_vagrant_virtualbox"] = {
            "compose_id": sc_vagrant_vbox[0][u'msg'][u'compose_id'],
            "name": sc_vagrant_vbox[0][u'msg'][u'image_name'],
            "release": sc_vagrant_vbox[0][u'msg'][u'release'],
            "image_name": image_name,
            "image_url": image_url,
        }

    return autocloud_info


def compose_manually_marked_bad(compose_id, bad_composes=MARK_ATOMIC_BAD_COMPOSES):
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
        mail_receivers=ATOMIC_EMAIL_RECIPIENTS,
        sender_email=ATOMIC_EMAIL_SENDER,
        sender_smtp=ATOMIC_EMAIL_SMTP):
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
A new update of Fedora Cloud Atomic Host has been released and can be
downloaded at:

Images can be found here:

    https://getfedora.org/en/cloud/download/atomic.html

Respective signed CHECKSUM files can be found here:
{}

Thank you,
Fedora Release Engineering
            """.format(
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
    except smtplib.SMTPException, e:
        print "ERROR: Unable to send email:\n{}\n".format(e)


def stage_atomic_release(
        compose_id,
        compose_basedir=COMPOSE_BASEDIR,
        testing_basedir=ATOMIC_TESTING_BASEDIR,
        dest_dir=ATOMIC_STABLE_DESTINATION):
    """
    stage_atomic_release

        stage the release somewhere, this will remove the old and rsync up the
        new twoweek release

    """

    source_loc = os.path.join(compose_basedir, compose_id, "compose")

    # FIXME - need sudo until pungi perms are fixed
    rsync_cmd = [
        'sudo',
        'rsync -avhHP --delete-after',
        '--link-dest={}'.format(
            os.path.join(
                testing_basedir,
                compose_id.split('-')[-1]
            )
        ),
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
        config['modname'] = ATOMIC_FEDMSG_MODNAME
        config['cert_prefix'] = ATOMIC_FEDMSG_CERT_PREFIX
        config['active'] = True

        # Send it.
        fedmsg.publish(topic=topic, msg=msg, **config)
    except Exception:
        # If you didn't know, log.exception automatically logs the traceback.
        log.exception("Failed to publish to fedmsg.")
        # But by passing, we don't let the exception bubble up and kill us.
        pass


def prune_old_testing_composes(
        prune_limit=ATOMIC_COMPOSE_PERSIST_LIMIT,
        prune_base_dir=ATOMIC_TESTING_BASEDIR):
    """
    prune_old_testing_composes

        Clean up old testing composes from /pub/alt/
    """

    prune_candidate_dirs = os.listdir(prune_base_dir)

    for testing_dir in prune_candidate_dirs[prune_limit:]:
        try:
            shutil.rmtree(
                os.path.join(prune_base_dir, testing_dir)
            )
        except OSError, e:
            log.error(
                "Error trying to remove directory: {}\n{}".format(
                    testing_dir,
                    e
                )
            )


if __name__ == '__main__':

    # get args from command line
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-k",
        "--key",
        help="signing key to use with sigul",
    )
    parser.add_argument(
        "-r",
        "--release",
        help="Fedora Release to target for release (Ex: 22, 23, 24, rawhide)",
    )
    pargs = parser.parse_args()

    if not pargs.key:
        log.error("No key passed, see -h for help")
        sys.exit(1)
    if not pargs.release:
        log.error("No release arg passed, see -h for help")
        sys.exit(1)

    log.info("Checking to make sure release is not currently blocked")
    if BLOCK_ATOMIC_RELEASE:
        log.info("Release Blocked: Exiting.")
        sys.exit(0)

    log.info("Querying datagrepper for latest AutoCloud successful tests")
    # Acquire the latest successful builds from datagrepper
    tested_autocloud_info = get_latest_successful_autocloud_test_info(
        pargs.release
    )
    log.info("Query to datagrepper complete")
    # If the dict is empty, there were no successful builds in the last two
    # weeks, error accordingly
    if not tested_autocloud_info:
        log.error("No successful builds found")
        sys.exit(2)

    log.info("Sending fedmsg releng.atomic.twoweek.begin")
    fedmsg_publish(
        topic="atomic.twoweek.begin",
        msg=dict(**tested_autocloud_info)
    )

    log.info("Extracting compose_id from tested autocloud data")
    compose_id = tested_autocloud_info['atomic_qcow2']['compose_id']

    log.info("Signing image metadata")
    sign_checksum_files(
        pargs.key,
        os.path.join(COMPOSE_BASEDIR, compose_id),
    )

    log.info("Staging release content in /pub/alt/atomic/stable/")
    stage_atomic_release(compose_id)

    log.info("Sending fedmsg releng.atomic.twoweek.complete")
    fedmsg_publish(
        topic="atomic.twoweek.complete",
        msg=dict(**tested_autocloud_info)
    )

    log.info("Sending Two Week Atomic announcement email")
    # Find all the Atomic images and CHECKSUM files to include in the email
    email_filelist = []
    for full_dir_path, _, short_names in os.walk(ATOMIC_STABLE_DESTINATION):
        for sname in fnmatch.filter(short_names, '*Atomic*'):
            email_filelist.append(
                os.path.join(
                    full_dir_path,
                    sname,
                )
            )
            for c_file in glob.glob(os.path.join(full_dir_path, "*CHECKSUM")):
                email_filelist.append(c_file)

    send_atomic_announce_email(set(email_filelist))

    log.info("Pruning old Atomic test composes")
    prune_old_testing_composes()

    log.info("Two Week Atomic Release Complete!")

    print("############REMINDER##########\n#\n#\n")
    print("Reset the block-release value to false in {}".format(
        "https://pagure.io/mark-atomic-bad"
    ))

# vim: set expandtab sw=4 sts=4 ts=4
