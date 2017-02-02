#!/usr/bin/python
#
# clean-amis.py - A utility to remove the nightly AMIs every 5 days.
#
#
# Authors:
#     Sayan Chowdhury <sayanchowdhury@fedoraproject.org>
# Copyright (C) 2016 Red Hat Inc,
# SPDX-License-Identifier:	GPL-2.0+

from __future__ import print_function

import os
import argparse
import boto.ec2
import fedfind
import fedfind.release
import requests

from datetime import datetime, timedelta

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

env = os.environ
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

DATAGREPPER_URL = 'https://apps.fedoraproject.org/datagrepper/'
NIGHTLY = 'nightly'

REGIONS = (
    'us-east-1',
    'us-west-2',
    'us-west-1',
    'eu-west-1',
    'eu-central-1',
    'ap-south-1',
    'ap-southeast-1',
    'ap-northeast-1',
    'ap-northeast-2',
    'ap-southeast-2',
    'sa-east-1',
)


def _get_raw_url():
    """ Get the datagrepper raw URL to fetch the message from
    """
    return DATAGREPPER_URL + '/raw'


def _get_nightly_amis_nd(delta, start=None, end=None):
    """ Returns the nightly AMIs for the last n days

    :args delta: last delta seconds
    """
    amis = []
    params = {
        'topic': 'org.fedoraproject.prod.fedimg.image.upload',
        'delta': delta,
        'rows_per_page': 100,
    }

    if start:
        params.update({'start': start})

    if end:
        params.update({'end': end})

    resp = requests.get(_get_raw_url(), params=params)
    messages = resp.json().get('raw_messages', [])
    print(messages)

    # Filter completed messages
    messages = [msg['msg']
                for msg in messages if msg['msg']['status'] == 'completed']

    for msg in messages:
        ami_id = msg['extra']['id']
        region = msg['destination']

        compose_id = msg['compose']['compose_id']
        compose_info = fedfind.release.get_release_cid(compose_id)
        compose_type = compose_info.type

        if compose_type == NIGHTLY:
            amis.append((compose_id, ami_id, region))

    return amis


def delete_amis_nd(amis, dry_run=False):
    """ Delete the give list of nightly AMIs

    :args amis: list of AMIs
    :args dry_run: dry run the flow
    """
    log.info('Deleting AMIs')
    for region in REGIONS:
        log.info('%s Starting' % region)
        # Create a connection to an AWS region
        conn = boto.ec2.connect_to_region(
            region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)
        log.info('%s: Connected' % region)

        # Filter all the nightly AMIs belonging to this region
        r_amis = [amis for _, _, r in amis if r == region]

        # Loop through the AMIs and delete then only if the launch permission
        # for the AMIs are private.
        for compose_id, ami_id, region in r_amis:
            try:
                ami_obj = conn.get_image(ami_id)
                is_launch_permitted = bool(ami_obj.get_launch_permission())
                if not dry_run and not is_launch_permitted:
                    conn.deregister_image(ami_obj.id, delete_snapshot=True)
                else:
                    print(ami_id)
            except:
                log.error('%s: %s failed' % (region, ami_id))


def change_amis_permission_nd(amis, dry_run=False):
    """ Change the launch permissions of the AMIs to private.

    The permission of the AMIs are changed to private first and then delete
    after 5 days.

    :args amis: list of AMIs
    :args dry_run: dry run the flow
    """
    log.info('Changing permission for AMIs')

    for region in REGIONS:
        log.info('%s: Starting' % region)
        # Create a connection to an AWS region
        conn = boto.ec2.connect_to_region(
            region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key)
        log.info('%s: Connected' % region)

        # Filter all the nightly AMIs belonging to this region
        r_amis = [amis for _, _, r in amis if r == region]

        # Loop through the AMIs change the permissions
        for _, ami_id, region in r_amis:
            try:
                if not dry_run:
                    conn.modify_image_attribute(ami_id,
                                                attribute='launchPermission',
                                                operation='remove',
                                                groups='all')
                else:
                    print(ami_id)
            except:
                log.error('%s: %s failed' % (region, ami_id))


if __name__ == '__main__':
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        "--delete",
        help="Delete the AMIs whose launch permissions have been removed",
        action="store_true", default=False)
    argument_parser.add_argument(
        "--change-perms",
        help="Change the launch permissions of the AMIs to private",
        action="store_true", default=False)
    argument_parser.add_argument(
        "--dry-run",
        help="Dry run the action to be performed",
        action="store_true", default=False)
    args = argument_parser.parse_args()

    if not args.delete and not args.change_perms:
        print('Either of the argument, delete or change permission is allowed')

    if args.delete and args.change_perms:
        print('Both the argument delete and change permission is not allowed')

    if args.delete:
        end = (datetime.now() - timedelta(days=5)).strftime('%s')
        amis = _get_nightly_amis_nd(delta=43200, end=int(end))
        delete_amis_nd(amis, dry_run=args.dry_run)

    if args.change_perms:
        amis = _get_nightly_amis_nd(delta=43200)
        change_amis_permission_nd(amis, dry_run=args.dry_run)
