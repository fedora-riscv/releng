#!/usr/bin/python -tt
#
# Copyright (C) 2013 Red Hat Inc,
# SPDX-License-Identifier:  GPL-2.0+
#
# Authors: Will Woods <wwoods@redhat.com>
#          Seth Vidal <skvidal@fedoraproject.org>
#          Robert Marshall <rmarshall@redhat.com>

from __future__ import print_function
import sys
import argparse
import shutil
from tempfile import mkdtemp
import dnf

class SackError(Exception):
    pass

major_version = sys.version_info[0]

# Set some constants
# Old definition
#critpath_groups = ['@core','@critical-path-base','@critical-path-gnome']
critpath_groups = [
    '@core', '@critical-path-apps', '@critical-path-base',
    '@critical-path-gnome', '@critical-path-kde', '@critical-path-lxde',
    '@critical-path-xfce'
]
primary_arches=('armhfp', 'x86_64')
alternate_arches=('i386','aarch64','ppc64','ppc64le','s390x')
# There is not current a programmatic way to generate this list
fakearch = {'i386':'i686', 'x86_64':'x86_64', 'ppc64':'ppc64', 'ppc':'ppc64', 'armhfp':'armv7hl', 'aarch64':'aarch64', 'ppc64le':'ppc64', 's390x':'s390x'}
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

for x in range(12,27,1):
    r = str(x)
    releasepath[r] = 'releases/%s/Everything/$basearch/os/' % r
    updatepath[r] = 'updates/%s/$basearch/' % r

# Branched Fedora goes here
branched = '27'
releasepath['branched'] = 'development/%s/Everything/$basearch/os' % branched
updatepath['branched'] = ''

# blacklists
blacklist = [ 'tzdata' ]

def get_source(pkg):
    return pkg.rsplit('-',2)[0]

provides_cache = {}
def resolve_deps(pkg, base):
    deps = []
    for prov in pkg.provides:
        provides_cache[prov] = pkg.name
    for req in pkg.requires:
        if req in provides_cache:
            deps.append(provides_cache[req])
            continue
        try:
            po = base.returnPackageByDep(req)
        except yum.Errors.YumBaseError:
            print("ERROR: unresolved dep for %s of pkg %s" % (req[0],
                  pkg.name))
            raise
        provides_cache[req] = po.name
        deps.append(po.name)
        for prov in po.provides:
            provides_cache[prov] = po.name

    return deps

def expand_yum_critpath(my, start_list):
    name_list = []
    # Expand the start_list to a list of names
    for name in start_list:
        if name.startswith('@'):
            print("expanding %s" % name)
            count = 0
            group = my.comps.return_group(name[1:])
            for groupmem in group.mandatory_packages.keys() + group.default_packages.keys():
                if groupmem not in name_list:
                    name_list.append(groupmem)
                    count += 1
            print("%s packages added" % count)
        else:
            if name not in name_list:
                name_list.append(name)
    # Iterate over the name_list
    count = 0
    pkg_list = []
    skipped_list = []
    handled = []

    while name_list:
        count += 1
        name = name_list.pop(0)
        handled.append(name)
        if name in blacklist:
            continue
        print("depsolving %4u done/%4u remaining (%s)" % (count, len(name_list), name))
        p = my.pkgSack.searchNevra(name=name)
        if not p:
            print("WARNING: unresolved package name: %s" % name)
            skipped_list.append(name)
            continue
        for pkg in p:
            pkg_list.append(pkg)
            for dep in resolve_deps(pkg, my):
                if dep not in handled and dep not in skipped_list and dep not in name_list:
                    print("    added %s" % dep)
                    name_list.append(dep)
    print("depsolving complete.")
    print("%u packages in critical path" % (count))
    print("%u rejected package names: %s" % (len(skipped_list),
                                             " ".join(skipped_list)))
    return pkg_list


def setup_yum(url=None, release=None, arch=None):
    my = yum.YumBase()
    basearch = getBaseArch()
    cachedir = mkdtemp(dir='/tmp', prefix='critpath-')
    if arch is None:
        arch = basearch
    elif arch != basearch:
        my.preconf.arch = fakearch[arch]
    my.conf.cachedir = cachedir
    my.conf.installroot = cachedir
    my.repos.disableRepo('*')
    if "/mnt/koji/compose/" not in args.url:
        my.add_enable_repo('critpath-repo-%s' % arch, baseurls=[url+releasepath[release]])
        print("adding critpath-repo-%s at %s" % (arch, url+releasepath[release]))
        if updatepath[release]:
            my.add_enable_repo('critpath-repo-updates-%s' % arch, baseurls=[url+updatepath[release]])
    else:
        my.add_enable_repo('critpath-repo-%s' % arch, baseurls=[url+'/$basearch/os/'])
        print("adding critpath-repo-%s at %s" % (arch, url+'/$basearch/os/'))
    return (my, cachedir)

def nvr(p):
    return '-'.join([p.name, p.ver, p.rel])

def expand_dnf_critpath(release):
    print("Resolving %s dependencies with DNF" % arch)
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
        print("Basearch: %s" % conf.basearch)
        print("Arch:     %s" % conf.arch)
        print("%s repo %s" % (arch, repo_url))

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

def solves_with_dnf(release_version):
    if release_version == 'branched':
        return True
    elif release_version == 'rawhide':
        return True
    elif release_version == 'devel':
        return True
    elif (int(release_version) > 26):
        return True
    else:
        return False


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
    parser.add_argument("--dnf", action='store_true', default=False,
                      help="Use DNF for dependency solving")
    args, extras = parser.parse_known_args()

    # Input & Sanity Validation
    if (len(extras) != 1) or (extras[0] not in releases):
        parser.error("must choose a release from the list: %s" % releases)

    # Parse values
    release = extras[0]
    check_arches = args.arches.split(',')
    alternate_check_arches = args.altarches.split(',')
    package_count = 0

    using_dnf = False
    if (args.dnf == True) or (major_version >= 3) or solves_with_dnf(release):
        using_dnf = True

    if not using_dnf:
        import yum
        from rpmUtils.arch import getBaseArch
        if yum.__version_info__ < (3, 2, 24) and args.arches != getBaseArch():
            print("WARNING: yum < 3.2.24 may be unable to depsolve other arches.")
            print("Get a newer yum or run this on an actual %s system." % args.arches)
            sys.exit(1)
    else:
        dnf_version = tuple(map(int, dnf.const.VERSION.split(".")))
        if dnf_version < (2, 0, 0):
            print("This script requires the DNF version 2.0 API.")
            sys.exit(1)


    if args.nvr and args.srpm:
        print("ERROR: --nvr and --srpm are mutually exclusive")
        sys.exit(1)

    if args.url != fedora_baseurl and "/mnt/koji/compose/" not in args.url:
        releasepath[release] = releasepath[release].replace('development/','')
        print("Using Base URL %s" % (args.url + releasepath[release]))
    else:
        print("Using Base URL %s" % (args.url))

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
        print("Expanding critical path for %s" % arch)
        my = None
        cachedir = None
        pkgs = None

        if using_dnf:
            pkgs = expand_dnf_critpath(release)
        else:
            print("Resolving %s dependencies with YUM" % arch)
            (my, cachedir) = setup_yum(url = url, release=release, arch=arch)
            pkgs = expand_yum_critpath(my, critpath_groups)

        if pkgs is None:
            package_count = 0
        else:
            package_count = len(pkgs)

        print("%u packages for %s" % (package_count, arch))

        if args.nvr:
            critpath.update([nvr(p).encode('utf8') for p in pkgs])
        elif args.srpm:
            critpath.update([get_source(p.sourcerpm) for p in pkgs])
        else:
            critpath.update([p.name.encode('utf8') for p in pkgs])

        del pkgs

        # deleting the cache dir has to happen after the above or
        # massive errors occur
        if not using_dnf:
            del my
            if cachedir.startswith("/tmp/"):
                shutil.rmtree(cachedir)
        print()
    # Write full list
    f = open(args.output,"wb")
    for packagename in sorted(critpath):
        f.write(packagename + b'\n')
    f.close()
    if critpath == None:
        package_count = 0
    else:
        package_count = len(critpath)
    print("Wrote %u items to %s" % (package_count, args.output))
