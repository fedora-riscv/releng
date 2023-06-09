#!/usr/bin/python

# Copyright (C) 2013 Red Hat Inc.
# SPDX-License-Identifier:	GPL-2.0+

from __future__ import print_function
import os
import shutil
from stat import *
import string
import sys
import tempfile
import re
import smtplib
import argparse
from yum.constants import *
from yum.misc import getCacheDir

# HAAACK
import imp
sys.modules['repoclosure'] = imp.load_source("repoclosure","/usr/bin/repoclosure")
import repoclosure

owners = {}
deps = {}

def generateConfig(distdir, treename, arch, testing=False):
    if not os.path.exists(os.path.join(distdir, arch)):
        return None
    if arch == 'source' or arch == 'SRPMS':
        return None
    if os.path.exists(os.path.join(distdir, arch, "os")):
        subdir = "os"
    else:
        subdir = ""
    if not os.path.exists(os.path.join(distdir, arch, subdir, "repodata", "repomd.xml")):
        return None

    (fd, conffile) = tempfile.mkstemp()

    if treename == 'epel-6':
        confheader = """
[main]
debuglevel=2
logfile=/var/log/yum.log
pkgpolicy=newest
distroverpkg=redhat-release
reposdir=/dev/null
keepcache=0
#exclude=kmod*,abrt*

[%s-%s]
name=Fedora EPEL %s Tree - %s
baseurl=file://%s/%s/%s
enabled=1

[rhel-server]
name=RHEL Server
baseurl=http://kojipkgs.fedoraproject.org/repo/rhel/rhel-%s-server-6/
enabled=1

[rhel-server-optional]
name=RHEL Server - optional
baseurl=http://kojipkgs.fedoraproject.org/repo/rhel/rhel-%s-server-optional-6/
enabled=1

[rhel6-ha]
name = rhel6 high availability for $basearch
baseurl=http://kojipkgs.fedoraproject.org/repo/rhel/rhel-$basearch-server-ha-6/
enabled=1

[rhel6-lb]
name = rhel6 load balancer for $basearch
baseurl=http://kojipkgs.fedoraproject.org/repo/rhel/rhel-$basearch-server-lb-6/
enabled=1

""" % (treename, arch, treename, arch, distdir, arch, subdir, arch, arch)

    # Enable the testing repos?
    # This block is the same for both el5 and el6.
    if testing:
        confheader += """
[%s-%s-testing]
name=Fedora EPEL %s Testing Tree - %s
baseurl=file://%s-testing/%s/%s
enabled=1

""" % (treename, arch, treename, arch, distdir, arch, subdir)
    os.write(fd, confheader)
    os.close(fd)
    return conffile


def libmunge(match):
    if match.groups()[1].isdigit():
        return "%s%d" % (match.groups()[0],int(match.groups()[1])+1)
    else:
        return "%s%s" % (match.groups()[0],match.groups()[1])

def addOwner(list, pkg):
    if list.get(pkg):
        return True

    if list.has_key(pkg):
        return False

    f = "%s-owner@fedoraproject.org" % pkg
    list[pkg] = f
    if f:
        return True
    return False

def getSrcPkg(pkg):
    if pkg.arch == 'src':
      return pkg.name
    srpm = pkg.returnSimple('sourcerpm')
    if not srpm:
        return None
    srcpkg = string.join(srpm.split('-')[:-2],'-')
    return srcpkg

def printableReq(pkg, dep):
    (n, f, v) = dep
    req = '%s' % n
    if f:
        flag = LETTERFLAGS[f]
        req = '%s %s' % (req, flag)
    if v:
        req = '%s %s' % (req, v)
    return "%s requires %s" % (pkg, req,)

def assignBlame(resolver, dep, guilty):
    def __addpackages(sack):
        for package in sack.returnPackages():
            p = getSrcPkg(package)
            if addOwner(guilty, p):
                list.append(p)
    
    # Given a dep, find potential responsible parties

    list = []
    
    # The dep itself
    list.append(dep)

    # Something that provides the dep
    __addpackages(resolver.whatProvides(dep, None, None))

    # Libraries: check for variant in soname
    if re.match("lib.*\.so\.[0-9]+",dep):
        new = re.sub("(lib.*\.so\.)([0-9]+)",libmunge,dep)
        __addpackages(resolver.whatProvides(new, None, None))
        libname = dep.split('.')[0]
        __addpackages(resolver.whatProvides(libname, None, None))

    return list

def generateSpam(pkgname, treename, sendmail = True):

    package = deps[pkgname]
    guilty = owners[pkgname]
    conspirators = []

    for s in package.keys():
        subpackage = package[s]
        for arch in subpackage.keys():
            brokendeps = subpackage[arch]
            for dep in brokendeps:
                for blame in dep[2]:
                    # We might not have an owner here for virtual deps
                    try:
                        party = owners[blame]
                    except:
                        continue
                    if party != guilty and party not in conspirators:
                        conspirators.append(party)

    data = """

%s has broken dependencies in the %s tree:
""" % (pkgname, treename)

    for s in package.keys():
        subpackage = package[s]
        for arch in subpackage.keys():
            data = data + "On %s:\n" % (arch)
            brokendeps = subpackage[arch]
            for dep in brokendeps:
                data = data + "\t%s\n" % printableReq(dep[0],dep[1])

    data = data + "Please resolve this as soon as possible.\n\n"
    
    fromaddr = 'buildsys@fedoraproject.org'
    toaddrs = [guilty]
    if conspirators:
        toaddrs = toaddrs + conspirators

    msg = """From: %s
To: %s
Cc: %s
Subject: Broken dependencies: %s

%s
""" % (fromaddr, guilty, string.join(conspirators,','), pkgname, data)
    if sendmail:
        try:
            server = smtplib.SMTP('localhost')
            server.set_debuglevel(1)
            server.sendmail(fromaddr, toaddrs, msg)
        except:
            print('sending mail failed')

def doit(dir, treename, mail=True, testing=False):
    for arch in os.listdir(dir):
        conffile = generateConfig(dir, treename, arch, testing)
        if not conffile:
            continue
        if arch == 'i386':
            carch = 'i686'
        elif arch == 'ppc':
            carch = 'ppc64'
        elif arch == 'sparc':
            carch = 'sparc64v'
        else:
            carch = arch
        my = repoclosure.RepoClosure(config = conffile, arch = [carch])
        cachedir = getCacheDir()
        my.repos.setCacheDir(cachedir)
        my.readMetadata()
        baddeps = my.getBrokenDeps(newest = False)
        pkgs = baddeps.keys()
        tmplist = [(x.returnSimple('name'), x) for x in pkgs]
        tmplist.sort()
        pkgs = [x for (key, x) in tmplist]
        if len(pkgs) > 0:
            print("Broken deps for %s" % (arch,))
            print("----------------------------------------------------------")
        for pkg in pkgs:
            if not pkg.repoid.startswith('epel'):
                continue
            srcpkg = getSrcPkg(pkg)

            addOwner(owners, srcpkg)

            if not deps.has_key(srcpkg):
                deps[srcpkg] = {}

            pkgid = "%s-%s" % (pkg.name, pkg.printVer())

            if not deps[srcpkg].has_key(pkgid):
                deps[srcpkg][pkgid] = {}

            broken = []
            for (n, f, v) in baddeps[pkg]:
                print("\t%s" % printableReq(pkg, (n, f, v)))

                blamelist = assignBlame(my, n, owners)

                broken.append( (pkg, (n, f, v), blamelist) )

            deps[srcpkg][pkgid][arch] = broken

        print("\n\n")
        os.unlink(conffile)
        shutil.rmtree(cachedir, ignore_errors = True)

    pkglist = deps.keys()
    for pkg in pkglist:
        generateSpam(pkg, treename, mail)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(usage = '%(prog)s [options] <directory>')
    parser.add_argument("--nomail", action="store_true")
    parser.add_argument("--enable-testing", action="store_true")
    parser.add_argument("--treename", default="rawhide")
    args, extras = parser.parse_known_args()

    if len(extras) != 1:
        parser.error("incorrect number of arguments")
        sys.exit(1)

    if args.nomail:
        mail = False
    else:
        mail = True

    if args.enable_testing:
        testing = True
    else:
        testing = False

    doit(extras[0], args.treename, mail, testing)
