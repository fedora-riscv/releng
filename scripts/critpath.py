#!/usr/bin/python3
#
# Copyright (C) 2013 Red Hat Inc,
# SPDX-License-Identifier:  GPL-2.0+
#
# Authors: Will Woods <wwoods@redhat.com>
#          Seth Vidal <skvidal@fedoraproject.org>
#          Robert Marshall <rmarshall@redhat.com>

import sys
import argparse
import shutil
from tempfile import mkdtemp
import dnf

class SackError(Exception):
    pass

# Set some constants
# Old definition
#CRITPATH_GROUPS = ['@core','@critical-path-base','@critical-path-gnome']
CRITPATH_GROUPS = [
    '@core', '@critical-path-apps', '@critical-path-base',
    '@critical-path-gnome', '@critical-path-kde', '@critical-path-lxde',
    '@critical-path-xfce'
]
PRIMARY_ARCHES=('armhfp', 'aarch64', 'x86_64')
ALTERNATE_ARCHES=('ppc64le','s390x')
FEDORA_BASEURL = 'http://dl.fedoraproject.org/pub/fedora/linux/'
FEDORA_ALTERNATEURL = 'http://dl.fedoraproject.org/pub/fedora-secondary/'
RELEASEPATH = {
    'devel': 'development/rawhide',
    'rawhide': 'development/rawhide'
}
UPDATEPATH = {
    'devel': '',
    'rawhide': ''
}

for r in range(12,37,1):
    RELEASEPATH[str(r)] = f'releases/{str(r)}'
    UPDATEPATH[str(r)] = f'updates/{str(r)}/$basearch/'

# Branched Fedora goes here, update the number when Branched number
# changes
RELEASEPATH['branched'] = 'development/37'
UPDATEPATH['branched'] = ''

def get_source(pkg):
    return pkg.rsplit('-',2)[0]

def nvr(p):
    return '-'.join([p.name, p.ver, p.rel])

def expand_dnf_critpath(url, arch):
    print(f"Resolving {arch} dependencies with DNF")
    base = dnf.Base()

    temp_cache_dir = mkdtemp(suffix='-critpath')
    temp_install_root = mkdtemp(suffix='-critpath-installroot')

    conf = base.conf
    # cache download data somewhere else
    conf.cachedir = temp_cache_dir
    # do not use the data from the previous runs of system dnf or groups will
    # be marked incorrectly
    conf.persistdir = temp_cache_dir
    conf.installroot = temp_install_root
    # dnf needs arches, not basearches to work
    if arch == "armhfp":
        conf.arch = "armv7hl"
    else:
        conf.arch = arch
    packages = set()

    try:
        # add a new repo requires an id, a conf object, and a baseurl
        repo_url = url + "/Everything/$basearch/os"

        # make sure we don't load the system repo and get local data
        print(f"Basearch: {conf.basearch}")
        print(f"Arch:     {conf.arch}")
        print(f"{arch} repo {repo_url}")

        # mark all critpath groups in base object
        for group in CRITPATH_GROUPS:
            base.reset(repos=True, goal=True, sack=True)
            base.repos.add_new_repo(arch, conf, baseurl=[repo_url])
            base.fill_sack(load_system_repo=False)
            if base.repos[arch].enabled is False:
                raise SackError

            # load up the comps data from configured repositories
            base.read_comps()
            group = group.replace('@','')
            base.group_install(group, ['mandatory', 'default', 'optional'], strict=False)
            # resolve the groups marked in base object
            base.resolve()
            packages = packages.union(base.transaction.install_set)

        return packages

    finally:
        base.close()
        del base
        del conf
        shutil.rmtree(temp_cache_dir)
        shutil.rmtree(temp_install_root)


def parse_args():
    releases = sorted(RELEASEPATH.keys())
    parser = argparse.ArgumentParser(usage = "%%(prog)s [options] [%s]" % '|'.join(releases))
    mexcgroup = parser.add_mutually_exclusive_group()
    mexcgroup.add_argument("--nvr", action='store_true', default=False,
                      help="output full NVR instead of just package name")
    mexcgroup.add_argument("--srpm", action='store_true', default=False,
                      help="Output source RPMS instead of binary RPMS (for pkgdb)")
    parser.add_argument("-a", "--arches", default=','.join(PRIMARY_ARCHES),
                      help="Primary arches to evaluate (%(default)s)")
    parser.add_argument("-s", "--altarches", default=','.join(ALTERNATE_ARCHES),
                      help="Alternate arches to evaluate (%(default)s)")
    parser.add_argument("-o", "--output", default="critpath.txt",
                      help="name of file to write critpath list (%(default)s)")
    parser.add_argument("-u", "--url", default=FEDORA_BASEURL,
                      help="URL to fedora/linux directory for primary arches")
    parser.add_argument("-r", "--alturl", default=FEDORA_ALTERNATEURL,
                      help="URL to fedora-secondary directory for alternate arches")
    parser.add_argument("-c", "--composeurl", required=False,
                      help="URL to a complete (not arch split) compose, overrides -u and -r")
    parser.add_argument("--noaltarch", action='store_true', default=False,
                      help="Not to run for alternate architectures")
    (args, extras) = parser.parse_known_args()

    # Input & Sanity Validation
    if (len(extras) != 1) or (extras[0] not in releases):
        parser.error(f"must choose a release from the list: {releases}")

    # Parse values
    release = extras[0]
    return(args, release)

def main():
    (args, release) = parse_args()
    check_arches = args.arches.split(',')
    if not (release.isdigit() and int(release) < 37):
        # armhfp is gone on F37+
        check_arches.remove("armhfp")
    alternate_check_arches = args.altarches.split(',')
    package_count = 0

    if args.composeurl:
        baseurl = args.composeurl
        alturl = args.composeurl
    else:
        baseurl = args.url + RELEASEPATH[release]
        alturl = args.alturl + RELEASEPATH[release]

    print(f"Using Base URL {baseurl}")
    print(f"Using alternate arch base URL {alturl}")

    # Do the critpath expansion for each arch
    critpath = set()
    for arch in check_arches+alternate_check_arches:
        url = baseurl
        if arch in alternate_check_arches:
            if args.noaltarch:
                continue
            url = alturl
        print(f"Expanding critical path for {arch}")
        pkgs = expand_dnf_critpath(url, arch)
        package_count = len(pkgs)

        print(f"{package_count} packages for {arch}")

        if args.nvr:
            critpath.update([nvr(p) for p in pkgs])
        elif args.srpm:
            critpath.update([get_source(p.sourcerpm) for p in pkgs])
        else:
            critpath.update([p.name for p in pkgs])

        del pkgs

        print()

    # Write full list
    with open(args.output, mode="w", encoding="utf-8") as outfh:
        for packagename in sorted(critpath):
            outfh.write(packagename + '\n')
    if critpath == None:
        package_count = 0
    else:
        package_count = len(critpath)
    print(f"Wrote {package_count} items to {args.output}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted, exiting...\n")
        sys.exit(1)
