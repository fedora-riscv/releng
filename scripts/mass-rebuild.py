#!/usr/bin/python3
#
# mass-rebuild.py - A utility to rebuild packages.
#
# Copyright (C) 2009-2013 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0+
#
# Authors:
#     Jesse Keating <jkeating@redhat.com>
#

from __future__ import print_function
import koji
import os
import subprocess
import sys
import operator

# contains info about all rebuilds, add new rebuilds there and update rebuildid
# here
from massrebuildsinfo import MASSREBUILDS

# Set some variables
# Some of these could arguably be passed in as args.
rebuildid = 'f40'
massrebuild = MASSREBUILDS[rebuildid]
user = 'Fedora Release Engineering <releng@fedoraproject.org>'
comment = 'Rebuilt for ' + massrebuild['wikipage']
workdir = os.path.expanduser('~/massbuild')
enviro = os.environ


# Define functions

# This function needs a dry-run like option
def buildmeoutput(cmd, action, pkg, env, cwd=workdir):
    """Simple function to run a command and return 0 for success, 1 for
       failure.  It also writes the taskID and name to a file and console.
       cmd is the command and arguments, action is aname for the action (for
       logging), pkg is the name of the packagebeing operated on, env is the
       environment dict, and cwd is where the script should be executed from."""

    try:
        output = subprocess.check_output(cmd, env=env, cwd=cwd).decode('utf-8').split()
        with open(workdir+"/taskID_file", 'a') as task_file:
            task_file.write('%s %s\n' % (pkg, output[2]))
        sys.stdout.write('  Successful submission: %s  taskID: %s\n' % (pkg, output[2]))
    except subprocess.CalledProcessError as e:
        sys.stderr.write('%s failed %s: %s\n' % (pkg, action, e))
        return 1
    return 0

# This function needs a dry-run like option
def runme(cmd, action, pkg, env, cwd=workdir):
    """Simple function to run a command and return 0 for success, 1 for
       failure.  cmd is a list of the command and arguments, action is a
       name for the action (for logging), pkg is the name of the package
       being operated on, env is the environment dict, and cwd is where
       the script should be executed from."""

    try:
        subprocess.check_call(cmd, env=env, cwd=cwd)
    except subprocess.CalledProcessError as e:
        sys.stderr.write('%s failed %s: %s\n' % (pkg, action, e))
        return 1
    return 0

# This function needs a dry-run like option
def runmeoutput(cmd, action, pkg, env, cwd=workdir):
    """Simple function to run a command and return output if successful. 
       cmd is a list of the command and arguments, action is a
       name for the action (for logging), pkg is the name of the package
       being operated on, env is the environment dict, and cwd is where
       the script should be executed from.  Returns 0 for failure"""

    try:
        pid = subprocess.Popen(cmd, env=env, cwd=cwd,
                               stdout=subprocess.PIPE, encoding='utf8')
    except BaseException as e:
        sys.stderr.write('%s failed %s: %s\n' % (pkg, action, e))
        return 0
    result = pid.communicate()[0].rstrip('\n')
    return result


# Environment for using releng credentials for pushing and building
enviro['GIT_SSH'] = '/usr/local/bin/relengpush'
koji_bin = '/usr/bin/compose-koji'

# Create a koji session
kojisession = koji.ClientSession('https://koji.fedoraproject.org/kojihub')

# Generate a list of packages to iterate over
pkgs = kojisession.listPackages(massrebuild['buildtag'], inherited=True)

# reduce the list to those that are not blocked and sort by package name
pkgs = sorted([pkg for pkg in pkgs if not pkg['blocked']],
              key=operator.itemgetter('package_name'))

print('Checking %s packages...' % len(pkgs))

# Loop over each package
for pkg in pkgs:
    name = pkg['package_name']
    id = pkg['package_id']

    # some package we just dont want to ever rebuild
    if name in massrebuild['pkg_skip_list']:
        print('Skipping %s, package is explicitely skipped')
        continue

    # Query to see if a build has already been attempted
    # this version requires newer koji:
    builds = kojisession.listBuilds(id, createdAfter=massrebuild['epoch'])
    newbuild = False
    # Check the builds to make sure they were for the target we care about
    for build in builds:
        try:
            buildtarget = kojisession.getTaskInfo(build['task_id'],
                                       request=True)['request'][1]
            if buildtarget == massrebuild['target'] or buildtarget in massrebuild['targets']:
                # We've already got an attempt made, skip.
                newbuild = True
                break
        except:
            print('Skipping %s, no taskinfo.' % name)
            continue
    if newbuild:
        print('Skipping %s, already attempted.' % name)
        continue

    # Check out git
    fedpkgcmd = ['fedpkg', '--user', 'releng', 'clone', '--branch', 'rawhide', name]
    print('Checking out %s' % name)
    if runme(fedpkgcmd, 'fedpkg', name, enviro):
        continue

    # Check for a checkout
    if not os.path.exists(os.path.join(workdir, name)):
        sys.stderr.write('%s failed checkout.\n' % name)
        continue

    # Check for a noautobuild file
    if os.path.exists(os.path.join(workdir, name, 'noautobuild')):
        # Maintainer does not want us to auto build.
        print('Skipping %s due to opt-out' % name)
        continue

    # Find the spec file
    files = os.listdir(os.path.join(workdir, name))
    spec = ''
    for file in files:
        if file.endswith('.spec'):
            spec = os.path.join(workdir, name, file)
            break

    if not spec:
        sys.stderr.write('%s failed spec check\n' % name)
        continue

    # rpmdev-bumpspec
    bumpspec = ['rpmdev-bumpspec', '-D', '-u', user, '-c', comment,
                os.path.join(workdir, name, spec)]
    print('Bumping %s' % spec)
    if runme(bumpspec, 'bumpspec', name, enviro):
        continue

    # Set the git user.name and user.email
    set_name = ['git', 'config', 'user.name', 'Fedora Release Engineering']
    set_mail = ['git', 'config', 'user.email', 'releng@fedoraproject.org']
    print('Setting git user.name and user.email')
    if runme(set_name, 'set_name', name, enviro,
                 cwd=os.path.join(workdir, name)):
        continue
    if runme(set_mail, 'set_mail', name, enviro,
                 cwd=os.path.join(workdir, name)):
        continue

    # git commit
    commit = ['git', 'commit', '-a', '-m', comment, '--allow-empty']
    print('Committing changes for %s' % name)
    if runme(commit, 'commit', name, enviro,
                 cwd=os.path.join(workdir, name)):
        continue
    # git push
    push = ['git', 'push']
    print('Pushing changes for %s' % name)
    if runme(push, 'push', name, enviro,
                 cwd=os.path.join(workdir, name)):
        continue


    # get git url
    urlcmd = ['fedpkg', 'giturl']
    print('Getting git url for %s' % name)
    url = runmeoutput(urlcmd, 'giturl', name, enviro,
                 cwd=os.path.join(workdir, name))
    if not url:
        continue

    # build
    build = [koji_bin, 'build', '--nowait', '--background', '--fail-fast', massrebuild['target'], url]
    print('Building %s' % name)
    buildmeoutput(build, 'build', name, enviro,
          cwd=os.path.join(workdir, name))
