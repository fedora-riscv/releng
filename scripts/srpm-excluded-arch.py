#!/usr/bin/python
# -*- coding: utf-8 -*-

# srpm-exlcuded-arch: is a tool to give you a list of packge names that
# are excluded on the given arches.  access to a srpm tree is needed.
#
# Copyright (C) 2008-2017 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0+
#
# Authors:
#       Dennis Gilmore <dennis@ausil.us>
#       Dan Horák <dhorak@redhat.com>

from __future__ import print_function
import rpm
import os
import sys
import argparse
import glob

parser = argparse.ArgumentParser()
parser.add_argument("--arches", "-a", help="space or command separated list of arches to check for", required=True)
parser.add_argument("--path", "-p", help="path to dir with srpms, default current directory", default=".")
parser.add_argument("--list", "-l", help="print one package per line", action="store_true")
args = parser.parse_args()

arches = args.arches
if arches.find(',') == -1:
    arches = arches.split(' ')
else:
    arches = arches.split(',')

srpms = glob.glob('%s/*/*.rpm' % args.path)
if len(srpms) == 0:
    print("Error: empty srpm list from directory '%s'" % (args.path))
    sys.exit(1)

pkglist = []

for srpm in srpms:
    """Return the rpm header."""
    ts = rpm.TransactionSet()
    ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES|rpm._RPMVSF_NODIGESTS)
    fo = file(str("%s" % (srpm)), "r")
    hdr = ts.hdrFromFdno(fo.fileno())
    fo.close()
    ExcludeArch = []
    for arch in arches:
        if arch in hdr[rpm.RPMTAG_EXCLUDEARCH]:
            ExcludeArch.append(arch)
        if not hdr[rpm.RPMTAG_EXCLUSIVEARCH] == []:
            if arch not in hdr[rpm.RPMTAG_EXCLUSIVEARCH]:
                if arch not in ExcludeArch:
                    ExcludeArch.append(arch)
    if ExcludeArch == arches:
        pkgname = hdr[rpm.RPMTAG_NAME]
        if pkgname not in pkglist:
            pkglist.append(pkgname)

if args.list:
    for pkg in pkglist:
        print(pkg)
else:
    output = ""
    for pkg in pkglist:
        output +=  pkg + " "

    print(output)
