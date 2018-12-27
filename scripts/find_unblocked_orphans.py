#! /usr/bin/python -tt
#
# find_unblocked_orphans.py - A utility to find orphaned packages in pagure
#                             that are unblocked in koji and to show what
#                             may require those orphans
#
# Copyright (c) 2009-2013 Red Hat
# SPDX-License-Identifier:	GPL-2.0
#
# Authors:
#     Jesse Keating <jkeating@redhat.com>
#     Till Maas <opensource@till.name>

from __future__ import print_function
from Queue import Queue
from collections import OrderedDict
from threading import Thread
import argparse
import datetime
import email.mime.text
import hashlib
import os
import smtplib
import sys
import textwrap
import traceback

import dnf
import dogpile.cache
import requests
import koji

try:
    import texttable
    with_table = True
except ImportError:
    with_table = False

try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache


cache = dogpile.cache.make_region().configure(
    'dogpile.cache.dbm',
    expiration_time=86400,
    arguments=dict(
        filename=os.path.expanduser('~/.cache/dist-git-orphans-cache.dbm')),
)
PAGURE_URL = 'https://src.fedoraproject.org'
PAGURE_MAX_ENTRIES_PER_PAGE = 100


EPEL6_RELEASE = dict(
    repo='https://kojipkgs.fedoraproject.org/mash/updates/dist-6E-epel/'
    'x86_64/',
    source_repo='https://kojipkgs.fedoraproject.org/mash/updates/'
    'dist-6E-epel/SRPMS',
    tag='dist-6E-epel',
    branch='el6',
    mailto='epel-announce@lists.fedoraproject.org',
    bcc=[],
)

EPEL7_RELEASE = dict(
    repo='https://kojipkgs.fedoraproject.org/mash/updates/epel7/x86_64/',
    source_repo='https://kojipkgs.fedoraproject.org/mash/updates/epel7/SRPMS',
    tag='epel7',
    branch='epel7',
    mailto='epel-announce@lists.fedoraproject.org',
    bcc=[],
)

RAWHIDE_RELEASE = dict(
    repo='https://kojipkgs.fedoraproject.org/compose/rawhide/'
         'latest-Fedora-Rawhide/compose/Everything/i386/os',
    source_repo='https://kojipkgs.fedoraproject.org/compose/rawhide/'
                'latest-Fedora-Rawhide/compose/Everything/source/tree/',
    tag='f30',
    branch='master',
    mailto='devel@lists.fedoraproject.org',
    bcc=[],
)

BRANCHED_RELEASE = dict(
    repo='https://kojipkgs.fedoraproject.org/compose/branched/'
         'latest-Fedora-29/compose/Everything/i386/os',
    source_repo='https://kojipkgs.fedoraproject.org/compose/branched/'
                'latest-Fedora-29/compose/Everything/source/tree/',
    tag='f29',
    branch='f29',
    mailto='devel@lists.fedoraproject.org',
    bcc=[],
)

RELEASES = {
    "rawhide": RAWHIDE_RELEASE,
    "branched": BRANCHED_RELEASE,
    "epel7": EPEL7_RELEASE,
    "epel6": EPEL6_RELEASE,
}

# pagure uid for orphan
ORPHAN_UID = 'orphan'

HEADER = """The following packages are orphaned or did not build for two
releases and will be retired when Fedora ({}) is branched, unless someone
adopts them. If you know for sure that the package should be retired, please do
so now with a proper reason:
https://fedoraproject.org/wiki/How_to_remove_a_package_at_end_of_life

According to https://fedoraproject.org/wiki/Schedule branching will
occur not earlier than 2014-07-08. The packages will be retired shortly before.
"""

HEADER = """The following packages are orphaned and will be retired when they
are orphaned for six weeks, unless someone adopts them. If you know for sure
that the package should be retired, please do so now with a proper reason:
https://fedoraproject.org/wiki/How_to_remove_a_package_at_end_of_life

Note: If you received this mail directly you (co)maintain one of the affected
packages or a package that depends on one. Please adopt the affected package or
retire your depending package to avoid broken dependencies, otherwise your
package will be retired when the affected package gets retired.
"""

FOOTER = """-- \nThe script creating this output is run and developed by Fedora
Release Engineering. Please report issues at its pagure instance:
https://pagure.io/releng/
The sources of this script can be found at:
https://pagure.io/releng/blob/master/f/scripts/find_unblocked_orphans.py
"""


def send_mail(from_, to, subject, text, bcc=None):
    if bcc is None:
        bcc = []

    msg = email.mime.text.MIMEText(text)
    msg["Subject"] = subject
    msg["From"] = from_
    msg["To"] = to
    if isinstance(to, basestring):
        to = [to]
    smtp = smtplib.SMTP('127.0.0.1')
    errors = smtp.sendmail(from_, to + bcc, msg.as_string())
    smtp.quit()
    return errors


class PagureInfo(object):
    def __init__(self, package, branch=RAWHIDE_RELEASE["branch"], ns='rpms'):
        self.package = package
        self.branch = branch

        try:
            response = requests.get(PAGURE_URL + '/api/0/' + ns + '/' + package)
            self.pkginfo = response.json()
            if 'error' in self.pkginfo:
                # This is likely a "project not found" 404 error.
                raise ValueError(self.pkginfo['error'])
        except Exception:
            sys.stderr.write(
                "Error getting pagure info for {}/{} on {}\n".format(
                    ns, package, branch))
            traceback.print_exc(file=sys.stderr)
            self.pkginfo = None
            return

    def get_people(self):
        if self.pkginfo is None:
            return []
        people = set()
        for kind in ['access_users', 'access_groups']:
            for persons in self.pkginfo[kind].values():
                for person in persons:
                    people.add(person)
        return list(sorted(people))

    @property
    def age(self):
        then = self.status_change
        now = datetime.datetime.utcnow()
        return now - then

    @property
    def status_change(self):
        if self.pkginfo is None:
            return datetime.datetime.utcnow()
        # See https://pagure.io/pagure/issue/2412
        if "date_modified" in self.pkginfo:
            status_change = float(self.pkginfo["date_modified"])
        else:
            status_change = float(self.pkginfo["date_created"])
        status_change = datetime.datetime.utcfromtimestamp(status_change)
        return status_change

    def __getitem__(self, *args, **kwargs):
        return self.pkginfo.__getitem__(*args, **kwargs)


def setup_dnf(repo=RAWHIDE_RELEASE["repo"],
              source_repo=RAWHIDE_RELEASE["source_repo"]):
    """ Setup dnf query with two repos
    """
    base = dnf.Base()
    # use digest to make repo id unique for each URL
    for baseurl, name in (repo, 'repo'), (source_repo, 'repo-source'):
        r = base.repos.add_new_repo(
            name + '-' + hashlib.sha256(baseurl).hexdigest(),
            base.conf,
            baseurl=[baseurl],
            skip_if_unavailable=False,
        )
        r.enable()
        r.load()

    base.fill_sack(load_system_repo=False, load_available_repos=True)
    return base.sack.query()


@cache.cache_on_arguments()
def orphan_packages(namespace='rpms'):
    pkgs, pages = get_pagure_orphans(namespace)
    for page in range(2, pages + 1):
        new_pkgs, _ = get_pagure_orphans(namespace, page)
        pkgs.update(new_pkgs)
    return pkgs


@cache.cache_on_arguments()
def get_pagure_orphans(namespace, page=1):
    url = PAGURE_URL + '/api/0/projects'
    params = dict(owner=ORPHAN_UID, namespace=namespace,
                  page=page,
                  per_page=PAGURE_MAX_ENTRIES_PER_PAGE)
    response = requests.get(url, params=params)
    if not bool(response):
        raise IOError("%r gave %r" % (response.request.url, response))
    pkgs = response.json()['projects']
    pages = response.json()['pagination']['pages']
    return dict([(p['name'], p) for p in pkgs]), pages


def unblocked_packages(packages, tagID=RAWHIDE_RELEASE["tag"]):
    unblocked = []
    kojisession = koji.ClientSession('https://koji.fedoraproject.org/kojihub')

    kojisession.multicall = True
    for p in packages:
        kojisession.listPackages(tagID=tagID, pkgID=p, inherited=True)
    listings = kojisession.multiCall()

    # Check the listings for unblocked packages.

    for pkgname, result in zip(packages, listings):
        if isinstance(result, list):
            [pkg] = result
            if pkg:
                if not pkg[0]['blocked']:
                    package_name = pkg[0]['package_name']
                    unblocked.append(package_name)
            else:
                # TODO - what state does this condition represent?
                pass
        else:
            print("ERROR: {pkgname}: {error}".format(
                pkgname=pkgname, error=result))
    return unblocked


class DepChecker(object):
    def __init__(self, release, repo=None, source_repo=None, namespace='rpms'):
        self._src_by_bin = None
        self._bin_by_src = None
        self.release = release
        if repo is None:
            repo = RELEASES[release]["repo"]

        if source_repo is None:
            source_repo = RELEASES[release]["source_repo"]

        dnfquery = setup_dnf(repo=repo, source_repo=source_repo)
        self.dnfquery = dnfquery
        self.pagureinfo_queue = Queue()
        self.pagure_dict = {}
        self.not_in_repo = []

    def create_mapping(self):
        src_by_bin = {}  # Dict of source pkg objects by binary package objects
        bin_by_src = {}  # Dict of binary pkgobjects by srpm name

        # Populate the dicts
        for rpm_package in self.dnfquery:
            if rpm_package.arch == 'src':
                continue
            srpm = self.SRPM(rpm_package)
            src_by_bin[rpm_package] = srpm
            if srpm.name in bin_by_src:
                bin_by_src[srpm.name].append(rpm_package)
            else:
                bin_by_src[srpm.name] = [rpm_package]

        self._src_by_bin = src_by_bin
        self._bin_by_src = bin_by_src

    @property
    def by_src(self):
        if not self._bin_by_src:
            self.create_mapping()
        return self._bin_by_src

    @property
    def by_bin(self):
        if not self._src_by_bin:
            self.create_mapping()
        return self._src_by_bin

    def find_dependent_packages(self, srpmname, ignore):
        """ Return packages depending on packages built from SRPM ``srpmname``
            that are built from different SRPMS not specified in ``ignore``.

            :param ignore: list of binary package names that will not be
                returned as dependent packages or considered as alternate
                providers
            :type ignore: list() of str()

            :returns: OrderedDict dependent_package: list of requires only
                provided by package ``srpmname`` {dep_pkg: [prov, ...]}
        """
        # Some of this code was stolen from repoquery
        dependent_packages = {}

        # Handle packags not found in the repo
        try:
            rpms = self.by_src[srpmname]
        except KeyError:
            # If we don't have a package in the repo, there is nothing to do
            sys.stderr.write(
                "Package {0} not found in repo\n".format(srpmname))
            self.not_in_repo.append(srpmname)
            rpms = []

        # provides of all packages built from ``srpmname``
        provides = []
        for pkg in rpms:
            # add all the provides from the package as strings
            string_provides = [str(prov) for prov in pkg.provides]
            provides.extend(string_provides)

            # add all files as provides
            # pkg.files is a list of paths
            # sometimes paths start with "//" instead of "/"
            # normalise "//" to "/":
            # os.path.normpath("//") == "//", but
            # os.path.normpath("///") == "/"
            file_provides = [os.path.normpath('//%s' % fn) for fn in pkg.files]
            provides.extend(file_provides)

        # Zip through the provides and find what's needed
        for prov in provides:
            # check only base provide, ignore specific versions
            # "foo = 1.fc20" -> "foo"
            base_provide = prov.split()[0]

            # FIXME: Workaround for:
            # https://bugzilla.redhat.com/show_bug.cgi?id=1191178
            if base_provide[0] == "/":
                base_provide = base_provide.replace("[", "?")
                base_provide = base_provide.replace("]", "?")

            # Elide provide if also provided by another package
            for pkg in self.dnfquery.filter(provides=base_provide):
                # FIXME: might miss broken dependencies in case the other
                # provider depends on a to-be-removed package as well
                if pkg.name in ignore:
                    #sys.stderr.write("Ignoring provider package %s\n" %
                    #                  pkg.name)
                    pass
                else:
                    break
            else:
                for dependent_pkg in self.dnfquery.filter(
                        requires=base_provide):
                    # skip if the dependent rpm package belongs to the
                    # to-be-removed Fedora package
                    if dependent_pkg in self.by_src[srpmname]:
                        continue

                    # skip if the dependent rpm package is also a
                    # package that should be removed
                    if dependent_pkg.name in ignore:
                        continue

                    # use setdefault to either create an entry for the
                    # dependent package or add the required prov
                    dependent_packages.setdefault(dependent_pkg, set()).add(
                        prov)
        return OrderedDict(sorted(dependent_packages.items()))

    def pagure_worker(self):
        branch = RELEASES[self.release]["branch"]
        while True:
            package = self.pagureinfo_queue.get()
            if package not in self.pagure_dict:
                pkginfo = PagureInfo(package, branch)
                sys.stderr.write("Got info for {} on {}, todo: {}\n".format(
                    package, branch, self.pagureinfo_queue.qsize()))
                self.pagure_dict[package] = pkginfo
            self.pagureinfo_queue.task_done()

    def recursive_deps(self, packages, max_deps=20):
        incomplete = []
        # Start threads to get information about (co)maintainers for packages
        for _ in range(0, 2):
            people_thread = Thread(target=self.pagure_worker)
            people_thread.daemon = True
            people_thread.start()
        # get a list of all rpm_pkgs that are to be removed
        rpm_pkg_names = []
        for name in packages:
            self.pagureinfo_queue.put(name)
            # Empty list if pkg is only for a different arch
            bin_pkgs = self.by_src.get(name, [])
            rpm_pkg_names.extend([p.name for p in bin_pkgs])

        # dict for all dependent packages for each to-be-removed package
        dep_map = OrderedDict()
        for name in sorted(packages):
            sys.stderr.write(
                "Getting packages depending on: {0}\n".format(name))
            ignore = rpm_pkg_names
            dep_map[name] = OrderedDict()
            to_check = [name]
            allow_more = True
            seen = []
            while True:
                sys.stderr.write("to_check ({}): {}\n".format(len(to_check),
                                                              repr(to_check)))
                check_next = to_check.pop(0)
                seen.append(check_next)
                dependent_packages = self.find_dependent_packages(check_next,
                                                                  ignore)
                if dependent_packages:
                    new_names = []
                    new_srpm_names = set()
                    for pkg, dependencies in dependent_packages.items():
                        if pkg.arch != "src":
                            srpm_name = self.by_bin[pkg].name
                        else:
                            srpm_name = pkg.name
                        if srpm_name not in to_check and \
                                srpm_name not in new_names and \
                                srpm_name not in seen:
                            new_names.append(srpm_name)
                        new_srpm_names.add(srpm_name)

                        for dep in dependencies:
                            dep_map[name].setdefault(
                                srpm_name,
                                OrderedDict()
                            ).setdefault(pkg, set()).add(dep)

                    for srpm_name in new_srpm_names:
                        self.pagureinfo_queue.put(srpm_name)

                    ignore.extend(new_names)
                    if allow_more:
                        to_check.extend(new_names)
                        found_deps = dep_map[name].keys()
                        dep_count = len(set(found_deps + to_check))
                        if dep_count > max_deps:
                            todo_deps = max_deps - len(found_deps)
                            if todo_deps < 0:
                                todo_deps = 0
                            incomplete.append(name)
                            sys.stderr.write(
                                "Dep count is {}\n".format(dep_count))
                            sys.stderr.write(
                                "incomplete is {}\n".format(incomplete))

                            allow_more = False
                            to_check = to_check[0:todo_deps]
                if not to_check:
                    break
            if not allow_more:
                sys.stderr.write("More than {0} broken deps for package "
                                 "'{1}', dependency check not"
                                 " completed\n".format(max_deps, name))

        sys.stderr.write("Waiting for (co)maintainer information...")
        self.pagureinfo_queue.join()
        sys.stderr.write("done\n")
        return dep_map, incomplete

    # This function was stolen from pungi
    def SRPM(self, package):
        """Given a package object, get a package object for the
        corresponding source rpm. Requires dnf still configured
        and a valid package object."""
        srpm = package.sourcerpm.split('.src.rpm')[0]
        (sname, sver, srel) = srpm.rsplit('-', 2)
        return srpm_nvr_object(self.dnfquery, sname, sver, srel)


@lru_cache(maxsize=2048)
def srpm_nvr_object(query, name, version, release):
    try:
        srpmpo = query.filter(name=name,
                              version=version,
                              release=release,
                              arch='src').run()[0]
        return srpmpo
    except IndexError:
        sys.stderr.write(
            "Error: Cannot find a source rpm for {}\n".format(srpm))
        sys.exit(1)


def maintainer_table(packages, pagure_dict):
    affected_people = {}

    if with_table:
        table = texttable.Texttable(max_width=80)
        table.header(["Package", "(co)maintainers", "Status Change"])
        table.set_cols_align(["l", "l", "l"])
        table.set_deco(table.HEADER)
    else:
        table = ""

    for package_name in packages:
        pkginfo = pagure_dict[package_name]
        people = pkginfo.get_people()
        for p in people:
            affected_people.setdefault(p, set()).add(package_name)
        p = ', '.join(people)
        age = pkginfo.age
        agestr = "{} weeks ago".format(age.days / 7)

        if with_table:
            table.add_row([package_name, p, agestr])
        else:
            table += "{} {} {}\n".format(package_name, p, agestr)

    if with_table:
        table = table.draw()
    return table, affected_people


def dependency_info(dep_map, affected_people, pagure_dict, incomplete):
    info = ""
    for package_name, subdict in dep_map.items():
        if subdict:
            pkginfo = pagure_dict[package_name]
            status_change = pkginfo.status_change.strftime("%Y-%m-%d")
            age = pkginfo.age.days / 7
            fmt = "Depending on: {} ({}), status change: {} ({} weeks ago)\n"
            info += fmt.format(package_name, len(subdict.keys()),
                               status_change, age)
            for fedora_package, dependent_packages in subdict.items():
                people = pagure_dict[fedora_package].get_people()
                for p in people:
                    affected_people.setdefault(p, set()).add(package_name)
                p = ", ".join(people)
                info += "\t{0} (maintained by: {1})\n".format(fedora_package,
                                                              p)
                for dep in dependent_packages:
                    provides = ", ".join(sorted(dependent_packages[dep]))
                    info += "\t\t%s requires %s\n" % (dep, provides)
                info += "\n"
        if package_name in incomplete:
            info += "\tToo many dependencies for {}, ".format(package_name)
            info += "not all listed here\n".format(package_name)
            info += "\n"
    return info


def maintainer_info(affected_people):
    info = ""
    for person in sorted(affected_people.iterkeys()):
        packages = affected_people[person]
        if person == ORPHAN_UID:
            continue
        info += "{0}: {1}\n".format(person, ", ".join(packages))
    return info


def package_info(unblocked, dep_map, depchecker, orphans=None, failed=None,
                 week_limit=6, release="", incomplete=[]):
    info = ""
    pagure_dict = depchecker.pagure_dict

    table, affected_people = maintainer_table(unblocked, pagure_dict)
    info += table
    info += "\n\nThe following packages require above mentioned packages:\n"
    info += dependency_info(dep_map, affected_people, pagure_dict, incomplete)

    info += "Affected (co)maintainers\n"
    info += maintainer_info(affected_people)

    if release:
        release_text = " ({})".format(release)
        branch = RELEASES[release]["branch"]
    else:
        release_text = ""

    wrapper = textwrap.TextWrapper(
        break_long_words=False, subsequent_indent="    ",
        break_on_hyphens=False
    )

    def wrap_and_format(label, pkgs):
        count = len(pkgs)
        text = "{} ({}): {}".format(label, count, " ".join(pkgs))
        wrappedtext = "\n" + wrapper.fill(text) + "\n\n"
        return wrappedtext

    if orphans:
        orphans = [o for o in orphans if o in unblocked]
        info += wrap_and_format("Orphans", orphans)

        orphans_breaking_deps = [o for o in orphans if dep_map.get(o)]
        info += wrap_and_format("Orphans (dependend on)",
                                orphans_breaking_deps)

        orphans_breaking_deps_stale = [
            o for o in orphans_breaking_deps if
            (pagure_dict[o].age.days / 7) >= week_limit]

        info += wrap_and_format(
            "Orphans{} for at least {} weeks (dependend on)".format(
                release_text, week_limit),
            orphans_breaking_deps_stale)

        orphans_not_breaking_deps = [o for o in orphans if not dep_map.get(o)]

        info += wrap_and_format("Orphans {}(not depended on)".format(
            release_text),
            orphans_not_breaking_deps)

        orphans_not_breaking_deps_stale = [
            o for o in orphans_not_breaking_deps if
            (pagure_dict[o].age.days / 7) >= week_limit]

        if orphans_not_breaking_deps_stale:
            sys.stderr.write("fedretire --orphan --branch {} -- {}\n".format(
                branch, " ".join(orphans_not_breaking_deps_stale)))

        info += wrap_and_format(
            "Orphans{} for at least {} weeks (not dependend on)".format(
                release_text, week_limit),
            orphans_not_breaking_deps_stale)

    breaking = set()
    for package, deps in dep_map.items():
        breaking = breaking.union(set(deps.keys()))

    if breaking:
        info += wrap_and_format("Depending packages" + release_text,
                                sorted(breaking))

        if orphans:
            reverse_deps = OrderedDict()
            stale_breaking = set()
            for package in orphans_breaking_deps_stale:
                for depender in dep_map[package]:
                    reverse_deps.setdefault(depender, []).append(package)
                stale_breaking = stale_breaking.union(
                    set(dep_map[package].keys()))
            for depender, providers in reverse_deps.items():
                sys.stderr.write("fedretire --orphan-dependent {} "
                                 "--branch {} -- {}\n".format(
                                     " ".join(providers), branch, depender
                                 ))
                for providingpkg in providers:
                    sys.stderr.write(
                        "fedretire --orphan --branch {} -- {}\n".format(
                            branch, providingpkg)
                    )
            info += wrap_and_format(
                "Packages depending on packages orphaned{} for more than "
                "{} weeks".format(release_text, week_limit),
                sorted(stale_breaking))

    if failed:
        ftbfs_label = "FTBFS" + release_text
        info += wrap_and_format(ftbfs_label, failed)

        ftbfs_breaking_deps = [o for o in failed if
                               o in dep_map and dep_map[o]]

        info += wrap_and_format(ftbfs_label + " (depended on)",
                                ftbfs_breaking_deps)

        ftbfs_not_breaking_deps = [o for o in failed if
                                   o not in dep_map or not dep_map[o]]

        info += wrap_and_format(ftbfs_label + " (not depended on)",
                                ftbfs_not_breaking_deps)

    if depchecker.not_in_repo:
        info += wrap_and_format("Not found in repo" + release_text,
                                sorted(depchecker.not_in_repo))

    addresses = ["{0}@fedoraproject.org".format(p)
                 for p in affected_people.keys() if p != ORPHAN_UID]
    return info, addresses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-orphans", dest="skip_orphans",
                        help="Do not look for orphans",
                        default=False, action="store_true")
    parser.add_argument("--release", choices=RELEASES.keys(),
                        default="rawhide")
    parser.add_argument("--mailto", default=None,
                        help="Send mail to this address (for testing)")
    parser.add_argument(
        "--send", default=False, action="store_true",
        help="Actually send mail including Bcc addresses to mailing list"
    )
    parser.add_argument("--source-repo", default=None,
                        help="Source repo URL to use for depcheck")
    parser.add_argument("--repo", default=None,
                        help="Repo URL to use for depcheck")
    parser.add_argument("--no-skip-blocked", default=True,
                        dest="skipblocked", action="store_false",
                        help="Do not skip blocked pkgs")
    parser.add_argument("--mailfrom", default="nobody@fedoraproject.org")
    parser.add_argument("failed", nargs="*",
                        help="Additional packages, e.g. FTBFS packages")
    args = parser.parse_args()
    failed = args.failed

    if args.source_repo is not None:
        RELEASES[args.release]["source_repo"] = args.source_repo

    if args.repo is not None:
        RELEASES[args.release]["repo"] = args.repo

    if args.skip_orphans:
        orphans = []
    else:
        # list of orphans from pagure
        sys.stderr.write('Contacting pagure for list of orphans...')
        orphans = sorted(orphan_packages())
        sys.stderr.write('done\n')

    sys.stderr.write('Getting builds from koji...')
    koji_tag = RELEASES[args.release]["tag"]
    allpkgs = sorted(list(set(list(orphans) + failed)))
    if args.skipblocked:
        unblocked = unblocked_packages(allpkgs, tagID=koji_tag)
    else:
        unblocked = allpkgs
    sys.stderr.write('done\n')

    text = HEADER.format(RELEASES[args.release]["tag"].upper())
    sys.stderr.write("Setting up dependency checker...")
    depchecker = DepChecker(args.release)
    sys.stderr.write("done\n")
    sys.stderr.write('Calculating dependencies...')
    # Create dnf object and depsolve out if requested.
    # TODO: add app args to either depsolve or not
    dep_map, incomplete = depchecker.recursive_deps(unblocked)
    sys.stderr.write('done\n')
    info, addresses = package_info(
        unblocked, dep_map, depchecker, orphans=orphans, failed=failed,
        release=args.release, incomplete=incomplete)
    text += "\n"
    text += info
    text += FOOTER
    print(text)

    if args.mailto or args.send:
        now = datetime.datetime.utcnow()
        today = now.strftime("%Y-%m-%d")
        subject = "Orphaned Packages in {} ({})".format(args.release, today)
        if args.mailto:
            mailto = args.mailto
        else:
            mailto = RELEASES[args.release]["mailto"]
        if args.send:
            bcc = addresses + RELEASES[args.release]["bcc"]
        else:
            bcc = None
        mail_errors = send_mail(args.mailfrom, mailto, subject, text, bcc)
        if mail_errors:
            sys.stderr.write("mail errors: " + repr(mail_errors) + "\n")

    sys.stderr.write("Addresses ({}): {}\n".format(len(addresses),
                                                   ", ".join(addresses)))

if __name__ == "__main__":
    main()
