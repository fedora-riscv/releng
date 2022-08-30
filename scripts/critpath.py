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
#critpath_groups = ['@core','@critical-path-base','@critical-path-gnome']
critpath_groups = [
    '@core', '@critical-path-apps', '@critical-path-base',
    '@critical-path-gnome', '@critical-path-kde', '@critical-path-lxde',
    '@critical-path-xfce'
]
primary_arches=('armhfp', 'aarch64', 'x86_64')
alternate_arches=('ppc64le','s390x')
# There is not current a programmatic way to generate this list
fakearch = {'i386':'i686', 'x86_64':'x86_64', 'ppc64':'ppc64', 'ppc':'ppc64', 'armhfp':'armv7hl', 'aarch64':'aarch64', 'ppc64le':'ppc64le', 's390x':'s390x'}
fedora_baseurl = 'http://dl.fedoraproject.org/pub/fedora/linux/'
fedora_alternateurl = 'http://dl.fedoraproject.org/pub/fedora-secondary/'
releasepath = {
    'devel': 'development/rawhide/Everything/$basearch/os/',
    'rawhide': 'development/rawhide/Everything/$basearch/os/'
}
updatepath = {
    'devel': '',
    'rawhide': ''
}

for x in range(12,37,1):
    r = str(x)
    releasepath[r] = f'releases/{r}/Everything/$basearch/os/'
    updatepath[r] = f'updates/{r}/$basearch/'

# Branched Fedora goes here
branched = '37'
releasepath['branched'] = f'development/{branched}/Everything/$basearch/os'
updatepath['branched'] = ''

def get_source(pkg):
    return pkg.rsplit('-',2)[0]

def nvr(p):
    return '-'.join([p.name, p.ver, p.rel])

def expand_dnf_critpath(release):
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
    conf.arch = fakearch[arch]

    try:
        packages = set()

        # add a new repo requires an id, a conf object, and a baseurl
        repo_url = url + releasepath[release]

        # make sure we don't load the system repo and get local data
        print(f"Basearch: {conf.basearch}")
        print(f"Arch:     {conf.arch}")
        print(f"{arch} repo {repo_url}")

        # mark all critpath groups in base object
        for group in critpath_groups:
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


    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print(message)
        print("DNF failed to synchronize the repository and cannot proceed.")
    finally:
        base.close()
        del base
        del conf
        shutil.rmtree(temp_cache_dir)
        shutil.rmtree(temp_install_root)


if __name__ == '__main__':
    # Option parsing
    releases = sorted(releasepath.keys())
    parser = argparse.ArgumentParser(usage = "%%(prog)s [options] [%s]" % '|'.join(releases))
    parser.add_argument("--nvr", action='store_true', default=False,
                      help="output full NVR instead of just package name")
    parser.add_argument("-a", "--arches", default=','.join(primary_arches),
                      help="Primary arches to evaluate (%(default)s)")
    parser.add_argument("-s", "--altarches", default=','.join(alternate_arches),
                      help="Alternate arches to evaluate (%(default)s)")
    parser.add_argument("-o", "--output", default="critpath.txt",
                      help="name of file to write critpath list (%(default)s)")
    parser.add_argument("-u", "--url", default=fedora_baseurl,
                      help="URL to Primary repos")
    parser.add_argument("-r", "--alturl", default=fedora_alternateurl,
                      help="URL to Alternate repos")
    parser.add_argument("--srpm", action='store_true', default=False,
                      help="Output source RPMS instead of binary RPMS (for pkgdb)")
    parser.add_argument("--noaltarch", action='store_true', default=False,
                      help="Not to run for alternate architectures")
    args, extras = parser.parse_known_args()

    # Input & Sanity Validation
    if (len(extras) != 1) or (extras[0] not in releases):
        parser.error(f"must choose a release from the list: {releases}")

    # Parse values
    release = extras[0]
    check_arches = args.arches.split(',')
    alternate_check_arches = args.altarches.split(',')
    package_count = 0

    if args.nvr and args.srpm:
        print("ERROR: --nvr and --srpm are mutually exclusive")
        sys.exit(1)

    if args.url != fedora_baseurl and "/mnt/koji/compose/" not in args.url:
        releasepath[release] = releasepath[release].replace('development/','')
        print(f"Using Base URL {args.url + releasepath[release]}")
    else:
        print(f"Using Base URL {args.url}")

    # Do the critpath expansion for each arch
    critpath = set()
    for arch in check_arches+alternate_check_arches:
        if arch in check_arches:
            url=args.url
        elif arch in alternate_check_arches:
            if args.noaltarch:
                continue
            else:
                if "/mnt/koji/compose/" not in args.url:
                    url = args.alturl
                else:
                    url = args.url
        else:
            raise Exception('Invalid architecture')
        print(f"Expanding critical path for {arch}")
        pkgs = None

        pkgs = expand_dnf_critpath(release)
        if pkgs is None:
            package_count = 0
        else:
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
    f = open(args.output, mode="w", encoding="utf-8")
    for packagename in sorted(critpath):
        f.write(packagename + '\n')
    f.close()
    if critpath == None:
        package_count = 0
    else:
        package_count = len(critpath)
    print(f"Wrote {package_count} items to {args.output}")
