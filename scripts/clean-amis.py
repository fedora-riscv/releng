#!/usr/bin/python3
#
# clean-amis.py - A utility to remove the nightly AMIs every 5 days.
#
#
# Authors:
#     Sayan Chowdhury <sayanchowdhury@fedoraproject.org>
# Copyright (C) 2016 Red Hat Inc,
# SPDX-License-Identifier:	GPL-2.0+
#
# The script runs as a cron job within the Fedora Infrastructure to delete
# the old AMIs. The permission of the selected AMIs are changed to private.
# This is to make sure that if someone from the community raises an issue
# we have the option to get the AMI back to public.
# After 10 days, if no complaints are raised the AMIs are deleted permanently.
#
# The complete process can be divided in couple of parts:
#
# - Fetching the data from datagrepper.
#   Based on the `--days` param, the script starts fetching the fedmsg messages
#   from datagrepper for the specified timeframe i.e. for lasts `n` days, where
#   `n` is the value of `--days` param. The queried fedmsg
#   topic `fedimg.image.upload`.
#
# - Selection of the AMIs:
#   After the AMIs are parsed from datagrepper. The AMIs are filtered to remove
#   Beta, Two-week Atomic Host and GA released AMIs.
#   Composes with `compose_type` set to `nightly` are picked up for deletion.
#   Composes which contain date in the `compose label` are also picked up for
#   deletion.
#   GA composes also have the compose_type set to production. So to distinguish
#   then we filter them if the compose_label have date in them. The GA
#   composes dont have date whereas they have the version in format of X.Y
#
# - Updated permissions of AMIs
#   The permissions of the selected AMIs are changed to private.
#
# - Deletion of AMIs
#   After 10 days, the private AMIs are deleted.

from __future__ import print_function

import os
import re
import argparse
import boto3
import functools
import fedfind
import fedfind.release
import libpagure
import requests

from datetime import datetime, timedelta, date

import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

env = os.environ
aws_access_key_id = os.environ.get("AWS_ACCESS_KEY")
aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")

pagure_access_token = os.environ.get("PAGURE_ACCESS_TOKEN")
instance_url = "https://pagure.io/"
repo_name = "ami-purge-report"
#
# Make the connection to Pagure
project = libpagure.Pagure(pagure_token=pagure_access_token,
                           repo_to=repo_name,
                           instance_url=instance_url)
no_auth_project = libpagure.Pagure(
                           repo_to=repo_name,
                           instance_url=instance_url)

DATAGREPPER_URL = "https://apps.fedoraproject.org/datagrepper/"
NIGHTLY = "nightly"

REGIONS = (
    "us-east-1",
    "us-east-2",
    "us-west-2",
    "us-west-1",
    "eu-west-1",
    "eu-central-1",
    "ap-south-1",
    "ap-southeast-1",
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-southeast-2",
    "sa-east-1",
    "ca-central-1",
    "eu-west-2",
)


def _is_timestamp_newer(timestamp1, timestamp2):
    """ Return true if timestamp1 is newer than timestamp2
    """
    timestamp1_f = datetime.strptime(timestamp1, "%d%m%Y")
    timestamp2_f = datetime.strptime(timestamp2, "%d%m%Y")

    return timestamp1_f > timestamp2_f


def _get_raw_url():
    """ Get the datagrepper raw URL to fetch the message from
    """
    return DATAGREPPER_URL + "/raw"


def get_page(page, delta, topic, start=None, end=None):

    params = {
        "topic": topic,
        "delta": delta,
        "rows_per_page": 100,
        "page": page,
    }

    if start:
        params.update({"start": start})

    if end:
        params.update({"end": end})

    resp = requests.get(_get_raw_url(), params=params)

    return resp.json()


def _get_two_week_released_atomic_compose_id(delta, start=None, end=None):
    """ Returns the release compose ids for last n days """

    topic = "org.fedoraproject.prod.releng.atomic.twoweek.complete"
    data = get_page(1, delta, topic, start, end)

    messages = data.get("raw_messages", [])

    for page in range(1, data["pages"]):
        data = get_page(
            topic=topic, page=page + 1, delta=delta, start=start, end=end
        )
        messages.extend(data["raw_messages"])

    messages = [msg["msg"] for msg in messages]

    released_atomic_compose_ids = []
    for msg in messages:
        # This is to support the older-format fedmsg messages
        if "atomic_raw" in msg:
            released_atomic_compose_ids.append(msg["atomic_raw"]["compose_id"])
        # We are just trying here multiple archs to get the compose id
        elif "aarch64" in msg:
            released_atomic_compose_ids.append(
                msg["aarch64"]["atomic_raw"]["compose_id"]
            )
        elif "x86_64" in msg:
            released_atomic_compose_ids.append(
                msg["x86_64"]["atomic_raw"]["compose_id"]
            )
        elif "ppc64le" in msg:
            released_atomic_compose_ids.append(
                msg["ppc64le"]["atomic_raw"]["compose_id"]
            )

    return set(released_atomic_compose_ids)


def _get_nightly_amis_nd(delta, start=None, end=None):
    """ Returns the nightly AMIs for the last n days

    :args delta: last delta seconds
    """
    amis = []
    released_atomic_compose_ids = _get_two_week_released_atomic_compose_id(
        delta=delta, start=start, end=end
    )

    topic = "org.fedoraproject.prod.fedimg.image.publish"
    data = get_page(1, delta, topic, start, end)
    messages = data.get("raw_messages", [])

    for page in range(1, data["pages"]):
        data = get_page(
            topic=topic, page=page + 1, delta=delta, start=start, end=end
        )
        messages.extend(data["raw_messages"])

    for message in messages:
        msg = message.get("msg")
        ami_id = msg["extra"]["id"]
        region = msg["destination"]

        compose_id = msg["compose"]
        compose_info = fedfind.release.get_release(cid=compose_id)
        compose_type = compose_info.type
        compose_label = compose_info.label

        # Sometimes the compose label is None or empty string
        # and they can be blindly put in for deletion
        if not compose_label:
            amis.append((compose_id, ami_id, region))

        if compose_id in released_atomic_compose_ids:
            continue

        # Include the nightly composes
        if compose_type == NIGHTLY:
            amis.append((compose_id, ami_id, region))
        else:
            # Include AMIs that have date in them
            # These are the production compose type but not GA
            result = re.search("-(\d{8}).", compose_label)
            if result is None:
                continue
            amis.append((compose_id, ami_id, region))

    return amis


def delete_amis_nd(deletetimestamp, dry_run=False):
    """ Delete the give list of nightly AMIs

    :args deletetimestamp: the timestamp for the delete
    :args dry_run: dry run the flow
    """
    log.info("Deleting AMIs")
    deleted_amis = []
    for region in REGIONS:
        log.info("%s Starting" % region)
        # Create a connection to an AWS region
        conn = boto3.client(
            "ec2",
            region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        log.info("%s: Connected" % region)

        response = {}
        try:
            response = conn.describe_images(
                Filters=[{"Name": "tag-key", "Values": ["LaunchPermissionRevoked"]}]
            )
        except Exception as ex:
            log.error("Failed to describe the images: %s\n%s" % (region, ex))

        amis = response.get("Images", [])

        for ami in amis:
            try:
                ami_id = ami["ImageId"]
                ami_name = ami['Name']
                is_launch_permitted = ami["Public"]
                _index = len(ami["BlockDeviceMappings"])
                snapshot_id = ami["BlockDeviceMappings"][0]["Ebs"]["SnapshotId"]
                tags = ami["Tags"]

                revoketimestamp = ""
                for tag in tags:
                    if "LaunchPermissionRevoked" in tag.values():
                        revoketimestamp = tag["Value"]

                if not revoketimestamp:
                    log.warn(
                        "%s ami has LaunchPermissionRevoked tag but no value"
                        % ami_id
                    )
                    continue

                if is_launch_permitted:
                    log.warn(
                        "%s ami has LaunchPermissionRevoked tag "
                        "but launch permission is still enabled" % ami_id
                    )
                    continue

                # The revoke timestamp allows us to tell how long ago an image
                # had permissions removed. If the permissions have been removed
                # for shorter than the waiting period then we can't delete it yet.
                if _is_timestamp_newer(revoketimestamp, deletetimestamp):
                    continue

                if not dry_run:
                    conn.deregister_image(ImageId=ami_id)
                    conn.delete_snapshot(SnapshotId=snapshot_id)
                    deleted_amis.append((ami_id, region, revoketimestamp, ami_name))
                else:
                    print(ami_id)
            except Exception as ex:
                log.error("%s: %s failed\n%s" % (region, ami_id, ex))

    return deleted_amis


def change_amis_permission_nd(amis, dry_run=False):
    """ Change the launch permissions of the AMIs to private.

    The permission of the AMIs are changed to private first and then delete
    after 5 days.

    :args amis: list of AMIs
    :args dry_run: dry run the flow
    """
    log.info("Changing permission for AMIs")
    todaystimestamp = date.today().strftime("%d%m%Y")
    changed_permission_amis = []

    for region in REGIONS:
        log.info("%s: Starting" % region)
        # Create a connection to an AWS region
        conn = boto3.client(
            "ec2",
            region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        log.info("%s: Connected" % region)

        # Filter all the nightly AMIs belonging to this region
        r_amis = [(c, a, r) for c, a, r in amis if r == region]
        r_amis_meta = [a for _, a, _ in r_amis]
        amis_meta = []
        try:
            if r_amis_meta:
                amis_meta = conn.describe_images(
                        ImageIds=r_amis_meta
                )
            else:
                continue
        except Exception as ex:
            log.error("Failed to describe the images: %s\n%s" % (region, ex))

            # We check if we queried any missing amis
            notexistamis = re.findall(r'\[([^]]*)\]', str(ex))
            if not notexistamis:
                continue

            notexistamis = notexistamis[0].split(", ")
            r_amis_meta = list(set(r_amis_meta) - set(notexistamis))
            if r_amis_meta:
                amis_meta = conn.describe_images(
                        ImageIds=r_amis_meta
                )
            else:
                log.error("No amis left to process: %s" % region)
                continue

        ami_info = {}
        for ami_meta in amis_meta['Images']:
            image_id = ami_meta["ImageId"]
            ami_info[image_id] = ami_meta['Name']

        # Loop through the AMIs change the permissions
        for ami_id in r_amis_meta:
            try:
                if not dry_run:
                    conn.modify_image_attribute(
                        ImageId=ami_id,
                        LaunchPermission={"Remove": [{"Group": "all"}]},
                    )
                    conn.create_tags(
                        Resources=[ami_id],
                        Tags=[
                            {
                                "Key": "LaunchPermissionRevoked",
                                "Value": todaystimestamp,
                            }
                        ],
                    )
                    name = ami_info.get('Name', '')
                    changed_permission_amis.append((ami_id, region, name))
                else:
                    print(ami_id)
            except Exception as ex:
                log.error("%s: %s failed \n %s" % (region, ami_id, ex))

    return changed_permission_amis


def generate_report_changed_permission(dg_amis, pc_amis):
    """ This is to generate the report via issue tracker in Pagure.

    :args dg_amis: list of AMIs that was generated from Datagrepper
    :args pc_amis: list of AMIs whose perms were actually changed.
    """
    log.info("Generating report for the day: Change Permissions")
    todaystimestamp = date.today().strftime("%d%m%Y")
    dg_output_string = []
    pc_output_string = []

    output_tmpl = """
{region}
---
{amis}
"""

    for region in REGIONS:
        r_amis = [a for c, a, r in dg_amis if r == region]
        dg_output_string.append(output_tmpl.format(
            region=region,
            amis='\n'.join(r_amis)
        ))

    for region in REGIONS:
        r_amis = ["%s - %s" % (a, n) for a, r, n in pc_amis if r == region]
        pc_output_string.append(output_tmpl.format(
            region=region,
            amis='\n'.join(r_amis)
        ))

    dg_output_string = "\n\n".join(dg_output_string)
    pc_output_string = "\n\n".join(pc_output_string)
    content = "Report for the run on {todaystimestamp}".format(
        todaystimestamp=todaystimestamp)

    create_issue_params = {
        'title': todaystimestamp,
        'content': content,
    }

    try:
        created_issue = project.create_issue(**create_issue_params)
        created_issue_id = created_issue['issue']['id']
    except Exception as ex:
        log.error("There was an error creating issue: %s" % ex)
        return

    # Comment the details of the AMIs fetched from datagrepper
    content = """
The list of AMIs that we fetch from Datagrepper
{dg_output_string}""".format(dg_output_string=dg_output_string)

    dg_params = {
        'issue_id': created_issue_id,
        'body': content,
    }
    try:
        project.comment_issue(**dg_params)
    except Exception as ex:
        log.error("There was an error creating issue: %s" % ex)

    # Comment the details of the AMIs whose permissions were changed.
    content = """
The list of AMIs whose permissions were changed.
{pc_output_string}""".format(pc_output_string=pc_output_string)

    pc_params = {
        'issue_id': created_issue_id,
        'body': content,
    }

    try:
        project.comment_issue(**pc_params)
    except Exception as ex:
        log.error("There was an error creating issue: %s" % ex)


def generate_report_delete(dl_amis):
    """ This is to generate the report via issue tracker in Pagure.

    :args dl_amis: list of AMIs that were deleted
    """
    log.info("Generating report for the day: Delete")
    todaystimestamp = date.today().strftime("%d%m%Y")
    created_issue_id = None
    dl_output_string = []

    output_tmpl = """
{region}
---
{amis}
"""

    for region in REGIONS:
        r_amis = ["%s - %s - %s" % (a, n, t) for a, r, t, n in dl_amis if r == region]
        dl_output_string.append(output_tmpl.format(
            region=region,
            amis='\n'.join(r_amis)
        ))

    dl_output_string = "\n\n".join(dl_output_string)

    issues = no_auth_project.list_issues()
    for issue in issues:
        if issue['title'] == todaystimestamp:
            created_issue_id = issue['id']
            break

    if created_issue_id is None:
        log.info("We could not find the request issue: %s" % todaystimestamp)
        return

    # Comment the details of the AMIs which were deleted
    content = """
The list of AMIs that were deleted.
{dl_output_string}""".format(dl_output_string=dl_output_string)

    dl_params = {
        'issue_id': created_issue_id,
        'body': content,
    }
    try:
        project.comment_issue(**dl_params)
    except Exception as ex:
        log.error("There was an error creating issue: %s" % ex)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        "--delete",
        help="Delete the AMIs whose launch permissions have been removed",
        action="store_true",
        default=False,
    )
    argument_parser.add_argument(
        "--days",
        help="Specify the number of days worth of AMI fedmsg information to fetch from datagrepper.",
        type=int,
    )
    argument_parser.add_argument(
        "--deletewaitperiod",
        help="Specify the number of days to wait after removing launch perms before deleting",
        type=int,
        default=10,
    )
    argument_parser.add_argument(
        "--permswaitperiod",
        help="Specify the number of days to wait before removing launch perms",
        type=int,
        default=10,
    )
    argument_parser.add_argument(
        "--change-perms",
        help="Change the launch permissions of the AMIs to private",
        action="store_true",
        default=False,
    )
    argument_parser.add_argument(
        "--dry-run",
        help="Dry run the action to be performed",
        action="store_true",
        default=False,
    )
    args = argument_parser.parse_args()

    if not args.delete and not args.change_perms:
        raise Exception(
            "Either of the argument, delete or change permission is required"
        )

    if args.delete and args.change_perms:
        raise Exception(
            "Both the argument delete and change permission is not allowed"
        )

    # Ideally, we could search through all the AMIs that ever were created but this
    # this would create huge load on datagrepper.
    # default to 4 weeks/ 28 days
    days = 28
    if args.days:
        days = args.days

    permswaitperiod = args.permswaitperiod
    deletewaitperiod = args.deletewaitperiod

    # The AMIs deleted are the nightly AMIs that are uploaded via fedimg everyday.
    # The clean up of the AMIs happens through a cron job.
    # The steps followed while deleting the AMIs:
    # - The selected AMIs are made private, so that if people report issue we can make it
    #   public again.
    # - If no issues are reported in 10 days, the AMIs are deleted permanently.

    if args.change_perms:
        if days < permswaitperiod:
            raise Exception(
                "permswaitperiod param cannot be more than days param"
            )
        end = (datetime.now() - timedelta(days=permswaitperiod)).strftime("%s")
        amis = _get_nightly_amis_nd(
           delta=86400 * (days - permswaitperiod), end=int(end)
        )
        perms_changed_amis = change_amis_permission_nd(amis, dry_run=args.dry_run)
        if not args.dry_run:
            generate_report_changed_permission(amis, perms_changed_amis)

    if args.delete:
        deletetimestamp = (
           datetime.now() - timedelta(days=deletewaitperiod)
        ).strftime("%d%m%Y")
        deleted_amis = delete_amis_nd(deletetimestamp, dry_run=args.dry_run)
        if not args.dry_run:
            generate_report_delete(deleted_amis)
