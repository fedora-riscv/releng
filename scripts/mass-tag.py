#!/usr/bin/python3
#
# mass-tag.py - A utility to tag rebuilt packages.
#
# Copyright (C) 2009-2023 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0+
#
# Authors:
#     Jesse Keating <jkeating@redhat.com>
#

from __future__ import print_function
import koji
import os
import operator
import argparse
import rpm

# Set some variables
# Some of these could arguably be passed in as args.
parser = argparse.ArgumentParser()
parser.add_argument('-t','--target', help='Tag to tag the builds into',required=True)
parser.add_argument('-s','--source',help='Tag holding the builds', required=True)
args = parser.parse_args()
target = args.target # tag to tag into
holdingtag = args.source # tag holding the rebuilds
newbuilds = {} # dict of packages that have a newer build in the target tag

# Create a koji session
koji_module = koji.get_profile_module("fedora")
kojisession = koji_module.ClientSession(koji_module.config.server)

# Log into koji
kojisession.gssapi_login()

# Generate a list of builds to iterate over, sorted by package name
builds = sorted(kojisession.listTagged(holdingtag, latest=True),
                key=operator.itemgetter('package_name'))

# Generate a list of packages in the target, reduced by not blocked.
pkgs = kojisession.listPackages(target, inherited=True)
pkgs = [pkg['package_name'] for pkg in pkgs if not pkg['blocked']]

print('Checking %s builds...' % len(builds))

# Use multicall
kojisession.multicall = True

# Loop over each build
for build in builds:
    # Get the latest tagged package in the target
    kojisession.listTagged(target, latest=True, package=build['package_name'])

# Get the results
results = kojisession.multiCall()

# Find builds that are newer in the target tag
kojisession.multicall = True
for build, [result] in zip(builds, results):
    if not build['package_name'] in pkgs:
        continue

    for newbuild in result:
        evr1 = (str(build['epoch'] or ''), build['version'], build['release'])
        evr2 = (str(newbuild['epoch'] or ''), newbuild['version'], newbuild['release'])
        if rpm.labelCompare(evr1, evr2) == -1:
            newbuilds.setdefault(build['package_name'], []).append(newbuild)

requests = kojisession.multiCall()

# Loop through the results and tag if necessary
kojisession.multicall = True
taglist = []
pkgcount = 0
for build in builds:
    if not build['package_name'] in pkgs:
        print('Skipping %s, blocked in %s' % (build['package_name'], target))
        continue

    if build['package_name'] in newbuilds:
        print('Newer build found for %s.' % build['package_name'])
    else:
        print('Tagging %s into %s' % (build['nvr'], target))
        taglist.append(build['nvr'])
        kojisession.tagBuildBypass(target, build)
        pkgcount += 1

    if pkgcount == 1000:
        print('Tagging %s builds.' % pkgcount)
        results = kojisession.multiCall()
        pkgcount = 0
        kojisession.multicall = True

print('Tagging %s builds.' % pkgcount)
results = kojisession.multiCall()
print('Tagged %s builds.' % len(taglist))

