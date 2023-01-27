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
from urllib.request import urlopen
import dnf


class SackError(Exception):
    pass


# Set some constants
# **IMPORTANT**: before adding any group to this list, ensure the
# corresponding decision context is in at least one policy in the
# Greenwave configuration:
# https://pagure.io/fedora-infra/ansible/blob/main/f/roles/openshift-apps/greenwave/templates/fedora.yaml
# bad things will happen if any update is in a critical path group
# with no corresponding greenwave policy. If no gating is required
# for packages in the group, the context only needs to be added to
# the "null" policies at the top of the file
CRITPATH_GROUPS = [
    "@core",
    "@critical-path-apps",
    "@critical-path-base",
    "@critical-path-deepin-desktop",
    "@critical-path-gnome",
    "@critical-path-kde",
    "@critical-path-lxde",
    "@critical-path-lxqt",
    "@critical-path-server",
    "@critical-path-standard",
    "@critical-path-xfce",
]
PRIMARY_ARCHES = ("armhfp", "aarch64", "x86_64")
ALTERNATE_ARCHES = ("ppc64le", "s390x")
BODHI_RELEASEURL = "https://bodhi.fedoraproject.org/releases/?rows_per_page=500"
FEDORA_BASEURL = "http://dl.fedoraproject.org/pub/fedora/linux/"
FEDORA_ALTERNATEURL = "http://dl.fedoraproject.org/pub/fedora-secondary/"
# used as a cache by get_bodhi_releases
BODHIRELEASES = {}


def get_bodhi_releases():
    global BODHIRELEASES
    if not BODHIRELEASES:
        bodhijson = json.loads(urlopen(BODHI_RELEASEURL).read().decode("utf8"))["releases"]
        devrels = {
            int(rel['version']) for rel in bodhijson if rel['state'] == 'pending' and
            rel['id_prefix'] == 'FEDORA' and rel["version"].isdigit()
        }
        if devrels:
            BODHIRELEASES[str(max(devrels))] = "rawhide"
        if len(devrels) > 1:
            BODHIRELEASES[str(min(devrels))] = "branched"
        stabrels = {
            int(rel['version']) for rel in bodhijson if rel['state'] == 'current' and
            rel['id_prefix'] == 'FEDORA' and rel["version"].isdigit()
        }
        for relnum in stabrels:
            BODHIRELEASES[str(relnum)] = "stable"
    return BODHIRELEASES


def get_paths(release):
    """This does a certain amount of fudging so we can refer to
    Branched by its release number or "branched", and Rawhide by its
    release number or "rawhide" or "devel".
    """
    relnums = get_bodhi_releases()
    if relnums.get(release) == "stable":
        return (
            f"releases/{release}/Everything/$basearch/os",
            f"updates/{release}/Everything/$basearch"
        )
    elif release in ("rawhide", "devel") or relnums.get(release) == "rawhide":
        return ("development/rawhide/Everything/$basearch/os", "")
    elif release == "branched" or relnums.get(release) == "branched":
        if release == "branched":
            try:
                release = [relnum for relnum in relnums if relnums[relnum] == "branched"][0]
            except IndexError:
                raise ValueError("Cannot find a branched release.")
        return (f"development/{release}/Everything/$basearch/os", "")
    raise ValueError(f"Unrecognized release {release}.")


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
    releases = sorted(get_bodhi_releases().keys())
    releases.extend(["branched", "devel", "rawhide", "all"])
    parser = argparse.ArgumentParser()
    mexcgroup = parser.add_mutually_exclusive_group()
    parser.add_argument(
        "release",
        choices=releases,
        help="The release to work on (a release number, 'branched', 'rawhide', or 'all'). In "
             "'all' mode, work on all current and pending releases, naming files in the format "
             "expected by Bodhi).",
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
        help="name of file to write flat plaintext critpath list (ignored for 'all') (%(default)s)",
    )
    parser.add_argument(
        "-j",
        "--jsonout",
        default="critpath.json",
        help="name of file to write grouped JSON critpath list (ignored for 'all') (%(default)s)",
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


def generate_critpath(release, args, output, jsonout):
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
        paths = get_paths(release)
        baseurl = args.url + paths[0]
        alturl = args.alturl + paths[0]
        if paths[1]:
            updateurl = args.url + paths[1]
            updatealturl = args.alturl + paths[1]

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

    write_files(critpath, output, jsonout)


def main():
    args = parse_args()
    release = args.release
    if release == "all":
        relnums = get_bodhi_releases()
        for release in relnums:
            print(f"Working on release {release}")
            # the name expected by Bodhi is '[gitbranchname].json';
            # for most releases this is 'f[relnum].json' but for
            # Rawhide it is 'rawhide.json'
            if relnums[release] == "rawhide":
                generate_critpath(release, args, "rawhide.txt", "rawhide.json")
            else:
                generate_critpath(release, args, f"f{release}.txt", f"f{release}.json")
    else:
        generate_critpath(release, args, args.output, args.jsonout)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted, exiting...\n")
        sys.exit(1)

# vim: set textwidth=100 ts=8 et sw=4:
