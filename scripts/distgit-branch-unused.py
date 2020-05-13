#!/usr/bin/python3

"""This script checks if a branch may be deleted.

A branch may be removed safely when, for all commits in that branch
not reachable from other branches, there are no complete koji builds.

Examples:

-\------A---\
  \----------\----- master

'A' has been merged into 'master', so it can be trivially deletected
without checking any builds.

  /---/-------\-B"-B'-B
-/---/---\-----\----master
          \--C

'B' has commits that are not found anywhere else (B, B', and B"), and
we need to check in koji if it knows about any builds from those
commits.
"""

import argparse
import pathlib
import pygit2
import koji as _koji

def find_hash(build):
    return build['source'].rsplit('#', 1)[1]

def list_builds(package, opts):
    koji = _koji.get_profile_module(opts.koji_profile)
    session_opts = koji.grab_session_options(koji.config)
    session = koji.ClientSession(koji.config.server, session_opts)

    pkg = session.getPackageID(package, strict=True)
    builds = session.listBuilds(packageID=pkg, state=koji.BUILD_STATES['COMPLETE'])

    with session.multicall(strict=True) as msession:
        for build in builds:
            if build['source'] is None:
                build['source'] = msession.getTaskInfo(build['task_id'], request=True)
    for build in builds:
        if isinstance(build['source'], koji.VirtualCall):
            build['source'] = build['source'].result['request'][0]

    by_hash = {find_hash(b):b for b in builds}
    return by_hash

def containing_branches(repo, commit, *, local, ignore_branch=None):
    if local:
        containing = repo.branches.local.with_commit(commit)
    else:
        containing = repo.branches.remote.with_commit(commit)

    for b in containing:
        branch = repo.branches[b]
        if branch != ignore_branch:
            yield branch

def name_in_spec_file(commit, package):
    try:
        spec = (commit.tree / f'{package}.spec').data
    except KeyError:
        print(f"Commit {commit.hex} doesn't have '{package}.spec', assuming package is unbuildable.")
        return None

    # We don't try to decode the whole spec file here, to reduce the chances of trouble.
    # Just any interesting lines.
    for line in spec.splitlines():
        if not line.startswith(b'Name:'):
            continue
        try:
            name = line[5:].decode().strip()
        except UnicodeDecodeError:
            print(f"Something is wrong: commit {commit.hex} has busted encoding'.")
            raise

        # Note that this does not do macro resolution. No need to support crazy things.
        return name

def do_opts():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--koji-profile', default='koji')
    parser.add_argument('--package')
    parser.add_argument('--repository', default='.', type=pathlib.Path)
    parser.add_argument('branch')

    opts = parser.parse_args()
    if opts.package is None:
        opts.package = opts.repository.absolute().name
    return opts

def branch_is_reachable(opts):
    repo = pygit2.Repository(opts.repository)
    try:
        branch = repo.branches.local[opts.branch]
        local = True
    except KeyError:
        branch = repo.branches.remote[opts.branch]
        local = False

    other = list(containing_branches(repo, branch.target, local=local, ignore_branch=branch))
    if other:
        names = ', '.join(o.name for o in other)
        print(f'Branch merged into {names}. Safe to delete.')
        return 0

    print('Branch has commits not found anywhere else. Looking for builds.')
    builds = list_builds(opts.package, opts)

    for n, commit in enumerate(repo.walk(branch.target, pygit2.GIT_SORT_TOPOLOGICAL)):
        subj = commit.message.splitlines()[0][:60]
        print(f'{n}: {commit.hex[:7]} {subj}')
        other = list(containing_branches(repo, commit, local=local, ignore_branch=branch))
        if other:
            names = ', '.join(o.name for o in other)
            print(f'Commit {commit.hex} referenced from {names}. Stopping iteration.')
            break

        # Figure out the name used in the spec file in that commit.
        # This is for the following case:
        # * Repo 'foo' exists and is active
        # * Repo 'foo2' (like a compat version of foo) exists and is active
        # * People have 'Name: foo' in 'foo2.spec' and make a build
        # * Koji will record this package as 'foo', even though it was built from 'foo2' repo
        try:
            real_name = name_in_spec_file(commit, opts.package)
        except UnicodeDecodeError:
            return 1
        if real_name is not None and real_name != opts.package:
            print(f"Sorry, {commit.hex} has Name:{real_name}, refusing to continue.")
            return 1

        built = builds.get(commit.hex, None)
        if built:
            print(f"Sorry, {commit.hex} built as {built['nvr']}.")
            koji_link = f"https://koji.fedoraproject.org/koji/taskinfo?taskID={built['task_id']}"
            print(f"See {koji_link}.")
            return 1

    print('No builds found, seems OK to delete.')
    return 0

if __name__ == '__main__':
    opts = do_opts()
    print(f'Checking package {opts.package} in {opts.repository.absolute()}')

    exit(branch_is_reachable(opts))
