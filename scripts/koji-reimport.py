#!/usr/bin/python
#
# koji-reimport.py: Reset builds and re-import corrupt noarch packages 
# on secondary kojis. 
#
# Copyright (c) 2014 Red Hat, Inc. 
#
# SPDX-License-Identifier: GPL-2.0
#
# Authors: 
#   David Aquilina <dwa@redhat.com>

import os
import subprocess
import koji
import tempfile
import shutil
import argparse

# fill these in: 
# pkgs to re-import: 
pkgs = ['']
# tag to tag them with: 
tag = ''

# setup koji sessions:
parser = argparse.ArgumentParser()
parser.add_argument('-p','--koji-profile', help='Koji profile for alternate arches',required=True)
args = parser.parse_args()
sec_profile = args.koji_profile

primarykoji = koji.get_profile_module("fedora")
secondarykoji = koji.get_profile_module(sec_profile)
primary = primarykoji.ClientSession(primarykoji.config.server)
secondary = secondarykoji.ClientSession(secondarykoji.config.server)
secondary.krb_login()

# do the thing: 

for pkg in pkgs: 
    print 'Parsing package '+pkg
    # get build info: 
    buildinfo = primary.getBuild(pkg)
    # reset the build on secondary: 
    secondary.untagBuild(tag, pkg)
    secondary.resetBuild(pkg)
    # create an empty build: 
    secondary.createEmptyBuild(buildinfo['package_name'], buildinfo['version'], buildinfo['release'], buildinfo['epoch'])
    # quick and dirty from here... 
    # create temporary dir, throw rpms into it: 
    tempdir = tempfile.mkdtemp() 
    subprocess.call(['koji', 'download-build', pkg], cwd=tempdir) 
    # verify RPMs are good, if so, import them:
    subprocess.check_call(['rpm -K *.rpm'], cwd=tempdir, shell=True)
    subprocess.call(['%s import *.rpm'%(sec_profile)], cwd=tempdir, shell=True)
    # Tag: 
    secondary.tagBuild(tag, pkg) 
    # Remove the temp dir
    shutil.rmtree(tempdir)

