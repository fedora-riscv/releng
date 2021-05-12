#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2017, 2021 Red Hat, Inc.
# License: GPLv2
# Author: Dan Horák <dhorak@redhat.com>
#
# Get statistics about waiting for builders from koji
#
# usage: koji-task-report.py [-h] [--channel CHANNEL] [--profile PROFILE] [--method METHOD] arch datefrom [dateto]
# ./koji-task-report.py s390x yesterday
# ./koji-task-report.py --channel compose --method runroot s390x today
#

import argparse
import koji
from datetime import datetime, timedelta

# get the date for tasks check from command line
parser = argparse.ArgumentParser()
parser.add_argument("arch", help="specific architecture to check for")
parser.add_argument("--channel", help="specific channel to check for", default="default")
parser.add_argument("--profile", help="koji profile (fedora, brew, stream)", default="fedora")
parser.add_argument("--method", help="method (BuildArch, runroot, ...)", default="buildArch")
parser.add_argument("datefrom", help="select tasks started since")
parser.add_argument("dateto", help="select tasks started till", nargs="?", default="now")
args = parser.parse_args()

koji_module = koji.get_profile_module(args.profile)
session = koji_module.ClientSession(koji_module.config.server)

channel = args.channel
channelinfo = session.getChannel(channel)

arches = []
if args.arch.find(',') > 0:
    arches = args.arch.split(',')
else:
    arches.append(args.arch)

opts = {}
opts['channel_id'] = channelinfo['id']
opts['createdAfter'] = args.datefrom
opts['createdBefore'] = args.dateto
opts['method'] = args.method
opts['arch'] = arches
# we want finished tasks
opts['state'] = [koji.TASK_STATES['CLOSED'], koji.TASK_STATES['FAILED']]

print(("\nReading completed '%s' Koji tasks in channel '%s' between %s and %s ...") % (args.profile, channel, opts['createdAfter'], opts['createdBefore']))
tasks = session.listTasks(opts)

total_waited = timedelta()
max_waited = timedelta()

for task in tasks:
    created = datetime.fromisoformat(task['create_time'])
    started = datetime.fromisoformat(task['start_time'])
    waited = started - created
    total_waited += waited
    if waited > max_waited:
        max_waited = waited

    print(("%s,%s") % (task['create_time'], waited))
#    print(("task id=%s\tcreated=%s\tstarted=%s") % (task['id'], task['create_time'], task['start_time']))

if len(tasks) > 0:
    print(("%s tasks, average waiting %s, maximum waiting %s") % (len(tasks), (total_waited/len(tasks)), max_waited))
else:
    print("no tasks found")

opts['state'] = [koji.TASK_STATES['OPEN']]
print(("\nReading running '%s' Koji tasks in channel '%s' between %s and %s ...") % (args.profile, channel, opts['createdAfter'], opts['createdBefore']))
tasks = session.listTasks(opts)
print(("%s tasks running") % (len(tasks)))


opts['state'] = [koji.TASK_STATES['FREE']]
print(("\nReading waiting '%s' Koji tasks in channel '%s' between %s and %s ...") % (args.profile, channel, opts['createdAfter'], opts['createdBefore']))
tasks = session.listTasks(opts)
print(("%s tasks waiting") % (len(tasks)))
