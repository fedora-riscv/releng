#!/usr/bin/python
#
# synd-blocked-primary.py - A utility to sync blocked packages in primary koji 
#                           to a secondary arch for a given tag
#
# Copyright (C) 2011-2013 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0
#
# Authors:
#     Dennis Gilmore <ausil@fedoraproject.org>

import koji
import os
import sys
import tempfile
import shutil

# Set some variables
# Some of these could arguably be passed in as args.
tags = ['f26', 'f25', 'f24', 'f23'] # tag to check in koji

arches = ['arm', 'ppc', 's390']

koji_module = koji.get_profile_module("fedora")
kojisession = koji_module.ClientSession(koji_module.config.server)

def getBlocked(kojisession, tag):
    blocked = [] # holding for blocked pkgs
    pkgs = kojisession.listPackages(tagID=tag)
    # Check the pkg list for blocked packages
    for pkg in pkgs:
        if pkg['blocked']:
            blocked.append(pkg['package_name'])
            #print "blocked package %s" % pkg['package_name']
    return blocked

def getUnBlocked(kojisession, tag):
    unblocked = [] # holding for blocked pkgs
    pkgs = kojisession.listPackages(tagID=tag)
    # Check the pkg list for blocked packages
    for pkg in pkgs:
        if not pkg['blocked']:
            unblocked.append(pkg['package_name'])
            #print "unblocked package %s" % pkg['package_name']
    return unblocked

for arch in arches:
    print "== Working on Arch: %s" % arch
    # Create a koji session
    sec_koji_module = koji.get_profile_module(args.arch)
    seckojisession = sec_koji_module.ClientSession(sec_koji_module.config.server)
    seckojisession.krb_login()

    for tag in tags:
        print "=== Working on tag: %s" % tag
        secblocked = [] # holding for blocked pkgs
        toblock = []
        unblock = []

        priblocked = getBlocked(kojisession, tag)
        secblocked = getBlocked(seckojisession, tag)
        priunblocked = getUnBlocked(kojisession, tag)
        secunblocked = getUnBlocked(seckojisession, tag)

        for pkg in priblocked:
            if pkg not in secblocked:
                toblock.append(pkg)
                print "need to block %s" % pkg
        
        for pkg in secblocked:
            if pkg not in priblocked:
                unblock.append(pkg)
                print "need to unblock %s" % pkg
        
        for pkg in priunblocked:
            if pkg not in secunblocked:
                unblock.append(pkg)
                print "need to unblock %s" % pkg
        
        seckojisession.multicall = True
        for pkg in toblock:
            print "Blocking: %s" % pkg
            seckojisession.packageListBlock(tag, pkg)

        for pkg in unblock:
            print "UnBlocking: %s" % pkg
            seckojisession.packageListUnblock(tag, pkg)


        listings = seckojisession.multiCall()

    seckojisession.logout()
# Print a blurb about where the code came from
print '\nThe script that generated this page can be found at '
print 'https://fedorahosted.org/rel-eng/browser/scripts/find-unblocked-orphans.py'
print 'There you can also report bugs and RFEs.'
