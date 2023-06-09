#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2013 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0
# Author: Dan Horák <dhorak@redhat.com>
#
# Compare the content of a tag between 2 koji instances
#


from __future__ import print_function
import sys
import os
import koji
import time
import string
import rpm 
import shutil

inherit = False
# get architecture and tag from command line
if len(sys.argv) > 2:
    SECONDARY_ARCH = sys.argv[1]
    tag = sys.argv[2]
    if len(sys.argv) > 3:
        inherit = True
else:
    print("Compare the content of a tag between 2 koji instances")
    print("Usage: %s <arch> <tag>" % sys.argv[0])
    exit(0)


LOCALKOJIHUB = 'https://%s.koji.fedoraproject.org/kojihub' % (SECONDARY_ARCH)
REMOTEKOJIHUB = 'https://koji.fedoraproject.org/kojihub'

def _rpmvercmp ((e1, v1, r1), (e2, v2, r2)):
    """find out which build is newer"""
    if e1 == "None":
        e1 = "0"
    if e2 == "None":
        e2 = "0"
    rc = rpm.labelCompare((e1, v1, r1), (e2, v2, r2))
    if rc == 1:
        #first evr wins
        return 1
    elif rc == 0:
        #same evr
        return 0
    else:
        #second evr wins
        return -1

def _countMissing (build):
    """find how many builds are missing in local koji"""
    builds = remotekojisession.listTagged(tag, inherit=inherit, package=build['package_name'])
    cnt = 0
    local_evr = (str(build['epoch']), build['version'], build['release'])


    for b in builds:
	remote_evr = (str(b['epoch']), b['version'], b['release'])
	newestRPM = _rpmvercmp(local_evr, remote_evr)
	if newestRPM == 0 or newestRPM == 1:
	    break
	cnt += 1
	if cnt > 5:
	    break

    return cnt

localkojisession = koji.ClientSession(LOCALKOJIHUB)
remotekojisession = koji.ClientSession(REMOTEKOJIHUB)

# package indexes
local = 0
remote = 0

cnt = {}
cnt['same'] = 0
cnt['newer'] = 0
cnt['older'] = 0
cnt['local_only'] = 0
cnt['remote_only'] = 0
cnt['total_missing_builds'] = 0

local_pkgs = sorted(localkojisession.listTagged(tag, inherit=inherit, latest=True), key = lambda pkg: pkg['package_name'])
remote_pkgs = sorted(remotekojisession.listTagged(tag, inherit=inherit, latest=True), key = lambda pkg: pkg['package_name'])

local_num = len(local_pkgs)
remote_num = len(remote_pkgs)


while (local < local_num) or (remote < remote_num):

    if remote_pkgs[remote]['package_name'] == local_pkgs[local]['package_name']:
        local_evr = (str(local_pkgs[local]['epoch']), local_pkgs[local]['version'], local_pkgs[local]['release'])
        remote_evr = (str(remote_pkgs[remote]['epoch']), remote_pkgs[remote]['version'], remote_pkgs[remote]['release'])

	newestRPM = _rpmvercmp(local_evr, remote_evr)
	if newestRPM == 0:
	    print("same: local and remote: %s " % local_pkgs[local]['nvr'])
	    cnt['same'] += 1
        if newestRPM == 1:
            print("newer locally: local: %s remote: %s" % (local_pkgs[local]['nvr'], remote_pkgs[remote]['nvr']))
	    cnt['newer'] += 1
        if newestRPM == -1:
	    missing = _countMissing(local_pkgs[local])
	    if missing > 5:
		txt = "more than 5"
	    else:
		txt = "%d" % missing

            print("newer remote: local: %s remote: %s with %s build(s) missing" % (local_pkgs[local]['nvr'], remote_pkgs[remote]['nvr'], txt))
	    cnt['total_missing_builds'] += missing
	    cnt['older'] += 1

	local += 1
	remote += 1

    elif remote_pkgs[remote]['package_name'] > local_pkgs[local]['package_name']:
    	print("only locally: %s" % local_pkgs[local]['nvr'])
	local += 1
	cnt['local_only'] += 1

    elif remote_pkgs[remote]['package_name'] < local_pkgs[local]['package_name']:
    	print("only remote: %s" % remote_pkgs[remote]['nvr'])
	remote += 1
	cnt['remote_only'] += 1

#    if cnt['older'] == 5:
#	break

print("statistics: %s" % cnt)
