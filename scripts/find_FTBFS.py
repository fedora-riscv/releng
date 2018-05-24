#!/usr/bin/python -tt
# vim: fileencoding=utf8
#
# find_FTBFS.py - Find FTBFS packages
#
# SPDX-License-Identifier:	GPL-2.0
#
# Authors:
#     Till Maas <opensource@till.name>
#
from __future__ import print_function
import argparse
import operator
import koji

from massrebuildsinfo import MASSREBUILDS

kojihub = 'https://koji.fedoraproject.org/kojihub'
kojisession = koji.ClientSession(kojihub)

parser = argparse.ArgumentParser()
parser.add_argument("--check-tag", default="f29", help="Tag to check")
parser.add_argument("--since-rebuild", default="f27",
                    help="Mass-rebuild to use as reference for cut-off date")
parser.add_argument("packages", nargs="*", metavar="package",
                    help="if specified, only check whether the specified "
                         "packages were not rebuild")

args = parser.parse_args()
massrebuild = MASSREBUILDS[args.since_rebuild]

if args.packages:
    all_koji_pkgs = args.packages
else:
    all_koji_pkgs = kojisession.listPackages(args.check_tag, inherited=True)

unblocked = sorted([pkg for pkg in all_koji_pkgs if not pkg['blocked']],
                   key=operator.itemgetter('package_name'))

kojisession.multicall = True
for pkg in unblocked:
    kojisession.listBuilds(pkg['package_id'],
                           state=koji.BUILD_STATES["COMPLETE"],
                           createdAfter=massrebuild['epoch'])

builds = kojisession.multiCall()

package_map = zip(unblocked, builds)
name_map = [(x['package_name'], b) for (x, b) in package_map]

# packages with no builds since epoch
unbuilt = [x for (x, b) in name_map if b == [[]]]

# remove packages that have never build, e.g. EPEL-only packages
kojisession.multicall = True
for pkg_name in unbuilt:
    kojisession.getLatestRPMS(args.check_tag, pkg_name)

last_builds = kojisession.multiCall()
last_builds_map = zip(unbuilt, last_builds)
ftbfs = [p for p, b in last_builds_map if b != [[[], []]]]

print("\n".join(ftbfs))
