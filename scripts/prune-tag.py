#!/usr/bin/python
#
# prune-tag.py - A utility to prune all but the latest build in a given tag.
#
# Copyright (C) 2009-2013 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0
#
# Authors:
#     Jesse Keating <jkeating@redhat.com>
#
# This program requires koji installed, as well as configured.

import os
import argparse
import sys
import koji
import logging

status = 0
builds = {}
untag = []
loglevel = ''
# Setup a dict of our key names as sigul knows them to the actual key ID
# that koji would use.  We should get this from sigul somehow.

# Create a parser to parse our arguments
parser = argparse.ArgumentParser(usage = '%(prog)s [options] tag')
parser.add_argument('-v', '--verbose', action='count', default=0,
                  help='Be verbose, specify twice for debug')
parser.add_argument('-n', '--dry-run', action='store_true', default=False,
                  help='Perform a dry run without untagging')
parser.add_argument('-p', '--koji-profile', default="fedora",
                  help='Select a koji profile to use')

KOJIHUB = args.koji_profile
# Get our options and arguments
args, extras =  parser.parse_known_args()

if args.verbose <= 0:
    loglevel = logging.WARNING
elif args.verbose == 1:
    loglevel = logging.INFO 
else: # options.verbose >= 2
    loglevel = logging.DEBUG


logging.basicConfig(format='%(levelname)s: %(message)s',
                    level=loglevel)

# Check to see if we got any arguments
if not extras:
    parser.print_help()
    sys.exit(1)

tag = extras[0]

# setup the koji session
logging.info('Setting up koji session')
koji_module = koji.get_profile_module(KOJIHUB)
kojisession = koji_module.ClientSession(koji_module.config.server)
if not kojisession.gssapi_login():
    logging.error('Unable to log into koji')
    sys.exit(1)

# Get a list of tagged packages
logging.info('Getting builds from %s' % tag)
tagged = kojisession.listTagged(tag)

logging.debug('Got %s builds' % len(builds))

# Sort builds by package
for b in tagged:
    builds.setdefault(b['package_name'], []).append(b)

# Find the packages with multiple builds
for pkg in sorted(builds.keys()):
    if len(builds[pkg]) > 1:
        logging.debug('Leaving newest build %s' % builds[pkg][0]['nvr'])
        for build in builds[pkg][1:]:
            logging.debug('Adding %s to untag list' % build['nvr'])
            untag.append(build['nvr'])

# Now untag all the builds
logging.info('Untagging %s builds' % len(untag))
if not args.dry_run:
    kojisession.multicall = True
for build in untag:
    if not args.dry_run:
        kojisession.untagBuildBypass(tag, build, force=True)
    logging.debug('Untagging %s' % build)

if not args.dry_run:
    results = kojisession.multiCall()

    for build, result in zip(untag, results):
        if isinstance(result, dict):
            logging.error('Error tagging %s' % build)
            if result['traceback']:
                logging.error('    ' + result['traceback'][-1])
            status = 1

logging.info('All done, pruned %s builds.' % len(untag))
sys.exit(status)
