#!/usr/bin/python
#
# isolate-tag.py - A utility to tag all inherited builds
#                      into a specific koji tag
#
# Copyright (C) 2010-2013 Red Hat Inc,
# SPDX-License-Identifier:      GPL-2.0
#
# Authors:
#     Nick Petrov <npetrov@redhat.com>


import koji
import os

tag = 'f23'

# Create a koji session
kojisession = koji.ClientSession('https://koji.fedoraproject.org/kojihub')

# Log into koji
clientcert = os.path.expanduser('~/.fedora.cert')
clientca = os.path.expanduser('~/.fedora-upload-ca.cert')
serverca = os.path.expanduser('~/.fedora-server-ca.cert')
kojisession.ssl_login(clientcert, clientca, serverca)

# Get all builds tagged into the tag w/o inherited builds
builds = kojisession.listTagged(tag, latest=True)

tagged = []
for build in builds:
    tagged.append(build['nvr'])

# Get all builds tagged to the tag including inherited builds
allbuilds = kojisession.listTagged(tag, latest=True, inherit=True)

# Isolate all the inherited builds
tagbuilds = []

for build in allbuilds:
    if build['nvr'] not in tagged:
        tagbuilds.append(build['nvr'])

kojisession.multicall = True
pkgcount = 0
batch = 1
# tag builds
for build in tagbuilds:
    pkgcount += 1
    print "tag %s into %s" % (build, tag)
    kojisession.tagBuildBypass(tag, build)
    if pkgcount == 1000:
        batch += 1
        print 'tagging %s builds' % pkgcount
        result = kojisession.multiCall()
        pkgcount = 0
        kojisession.multicall = True

print 'Tagging %s builds.' % pkgcount
print 'Tagged %s batches' % batch

result = kojisession.multiCall()

