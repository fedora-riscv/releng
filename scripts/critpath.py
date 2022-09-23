#!/usr/bin/python3
#
# Copyright (C) 2013 Red Hat Inc,
# SPDX-License-Identifier:  GPL-2.0+
#
# Authors: Will Woods <wwoods@redhat.com>
#          Seth Vidal <skvidal@fedoraproject.org>
#          Robert Marshall <rmarshall@redhat.com>
#          Adam Williamson <awilliam@redhat.com>

# this is a script, not a public module, we don't need docstrings
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring

import sys
import argparse
from collections import defaultdict
import json
import shutil
from tempfile import mkdtemp
import dnf


class SackError(Exception):
    pass


# Set some constants
# Old definition
# CRITPATH_GROUPS = ['@core','@critical-path-base','@critical-path-gnome']
CRITPATH_GROUPS = [
    "@core",
    "@critical-path-apps",
    "@critical-path-base",
    "@critical-path-gnome",
    "@critical-path-kde",
    "@critical-path-lxde",
    "@critical-path-xfce",
]
PRIMARY_ARCHES = ("armhfp", "aarch64", "x86_64")
ALTERNATE_ARCHES = ("ppc64le", "s390x")
FEDORA_BASEURL = "http://dl.fedoraproject.org/pub/fedora/linux/"
FEDORA_ALTERNATEURL = "http://dl.fedoraproject.org/pub/fedora-secondary/"
RELEASEPATH = {
    "devel": "development/rawhide/Everything/$basearch/os",
    "rawhide": "development/rawhide/Everything/$basearch/os",
}
UPDATEPATH = {"devel": "", "rawhide": ""}

# the numbers here are "oldest active stable release" and "Branched
# number (or Rawhide number if no Branched)"; Python ranges exclude
# the top limiter so this is "all current stable releases"
for r in range(35, 37, 1):
    RELEASEPATH[str(r)] = f"releases/{str(r)}/Everything/$basearch/os"
    UPDATEPATH[str(r)] = f"updates/{str(r)}/Everything/$basearch"

# Branched Fedora goes here, update the number when Branched number
# changes
RELEASEPATH["branched"] = "development/37/Everything/$basearch/os"
UPDATEPATH["branched"] = ""


def get_source(pkg):
    return pkg.rsplit("-", 2)[0]


def nvr(pkg):
    return "-".join([pkg.name, pkg.ver, pkg.rel])


def expand_dnf_critpath(urls, arch):
    print(f"Resolving {arch} dependencies with DNF")
    base = dnf.Base()

    temp_cache_dir = mkdtemp(suffix="-critpath")
    temp_install_root = mkdtemp(suffix="-critpath-installroot")

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
    packages = dict()

    try:
        # add a new repo requires an id, a conf object, and a baseurl
        # make sure we don't load the system repo and get local data
        print(f"Basearch: {conf.basearch}")
        print(f"Arch:     {conf.arch}")
        for url in urls:
            print(f"Repo:     {url}")

        # mark all critpath groups in base object
        for group in CRITPATH_GROUPS:
            base.reset(repos=True, goal=True, sack=True)
            repoids = []
            for (num, url) in enumerate(urls):
                repoid = arch + str(num)
                repoids.append(repoid)
                base.repos.add_new_repo(repoid, conf, baseurl=[url])
            base.fill_sack(load_system_repo=False)
            for repoid in repoids:
                if base.repos[repoid].enabled is False:
                    raise SackError

            # load up the comps data from configured repositories
            base.read_comps()
            group = group.replace("@", "")
            base.group_install(group, ["mandatory", "default", "optional"], strict=False)
            # resolve the groups marked in base object
            base.resolve()
            packages[group] = base.transaction.install_set

        return packages

    finally:
        base.close()
        del base
        del conf
        shutil.rmtree(temp_cache_dir)
        shutil.rmtree(temp_install_root)


def parse_args():
    releases = sorted(RELEASEPATH.keys())
    parser = argparse.ArgumentParser()
    mexcgroup = parser.add_mutually_exclusive_group()
    parser.add_argument(
        "release",
        choices=releases,
        help="The release to work on (a release number, 'branched', or 'rawhide')",
    )
    mexcgroup.add_argument(
        "--nvr",
        action="store_true",
        default=False,
        help="output full NVR instead of just package name",
    )
    mexcgroup.add_argument(
        "--srpm",
        action="store_true",
        default=False,
        help="Output source RPMS instead of binary RPMS (for uploading to PDC)",
    )
    parser.add_argument(
        "-a",
        "--arches",
        default=",".join(PRIMARY_ARCHES),
        help="Primary arches to evaluate (%(default)s)",
    )
    parser.add_argument(
        "-s",
        "--altarches",
        default=",".join(ALTERNATE_ARCHES),
        help="Alternate arches to evaluate (%(default)s)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="critpath.txt",
        help="name of file to write flat plaintext critpath list (%(default)s)",
    )
    parser.add_argument(
        "-j",
        "--jsonout",
        default="critpath.json",
        help="name of file to write grouped JSON critpath list (%(default)s)",
    )
    parser.add_argument(
        "-u",
        "--url",
        default=FEDORA_BASEURL,
        help="URL to fedora/linux directory for primary arches",
    )
    parser.add_argument(
        "-r",
        "--alturl",
        default=FEDORA_ALTERNATEURL,
        help="URL to fedora-secondary directory for alternate arches",
    )
    parser.add_argument(
        "-c",
        "--composeurl",
        required=False,
        help="URL to a complete (not arch split) compose, overrides -u and -r",
    )
    parser.add_argument(
        "--noaltarch",
        action="store_true",
        default=False,
        help="Not to run for alternate architectures",
    )
    return parser.parse_args()


def write_files(critpath, outpath, jsonout):
    wrapped = {"rpm": critpath}
    with open(jsonout, mode="w", encoding="utf-8") as jsonoutfh:
        json.dump(wrapped, jsonoutfh, sort_keys=True, indent=4)
    print(f"Wrote grouped critpath data to {jsonout}")
    pkgs = set()
    for grppkgs in critpath.values():
        pkgs = pkgs.union(set(grppkgs))
    with open(outpath, mode="w", encoding="utf-8") as outfh:
        for packagename in sorted(pkgs):
            outfh.write(packagename + "\n")
    package_count = len(pkgs)
    print(f"Wrote {package_count} items to {outpath}")


def main():
    args = parse_args()
    release = args.release
    check_arches = args.arches.split(",")
    if not (release.isdigit() and int(release) < 37):
        # armhfp is gone on F37+
        check_arches.remove("armhfp")
    alternate_check_arches = args.altarches.split(",")
    package_count = 0

    updateurl = None
    updatealturl = None
    if args.composeurl:
        baseurl = args.composeurl + "/Everything/$basearch/os"
        alturl = args.composeurl + "/Everything/$basearch/os"
    else:
        baseurl = args.url + RELEASEPATH[release]
        alturl = args.alturl + RELEASEPATH[release]
        if UPDATEPATH[release]:
            updateurl = args.url + UPDATEPATH[release]
            updatealturl = args.alturl + UPDATEPATH[release]

    print(f"Using Base URL {baseurl}")
    print(f"Using alternate arch base URL {alturl}")
    if updateurl:
        print(f"Using update URL {updateurl}")
    if updatealturl:
        print(f"Using alternate arch update URL {updatealturl}")

    # Do the critpath expansion for each arch
    critpath = defaultdict(set)
    for arch in check_arches + alternate_check_arches:
        urls = [baseurl, updateurl]
        if arch in alternate_check_arches:
            if args.noaltarch:
                continue
            urls = [alturl, updatealturl]
        # strip None update URLs when we're not using them
        urls = [url for url in urls if url]

        print(f"Expanding critical path for {arch}")
        pkgdict = expand_dnf_critpath(urls, arch)

        for (group, pkgs) in pkgdict.items():
            package_count = len(pkgs)
            print(f"{package_count} packages in {group} for {arch}")

            if args.nvr:
                critpath[group].update([nvr(pkg) for pkg in pkgs])
            elif args.srpm:
                critpath[group].update([get_source(pkg.sourcerpm) for pkg in pkgs])
            else:
                critpath[group].update([pkg.name for pkg in pkgs])

        del pkgdict
        print()
    # Turn sets back into lists (so we can JSON-dump them)
    for group in critpath:
        critpath[group] = sorted(critpath[group])

    write_files(critpath, args.output, args.jsonout)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted, exiting...\n")
        sys.exit(1)

# vim: set textwidth=100 ts=8 et sw=4:
