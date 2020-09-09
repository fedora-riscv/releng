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
import re
import subprocess
import pygit2
import requests
import koji as _koji

BODHI_RELEASES = 'https://bodhi.fedoraproject.org/releases/?rows_per_page=1000'
NORMAL_BRANCHES = r'^(f\d{1,2}|el\d|epel\d|epel1\d)$'

MACRO_DEF_RE = re.compile(rb'^%(global|define)\s+(?P<macro>\S+)\s+(?P<value>.+)$')

_KOJI_SESSION = None
def koji_session(opts):
    global _KOJI_SESSION
    if not _KOJI_SESSION:
        koji = _koji.get_profile_module(opts.koji_profile)
        session_opts = koji.grab_session_options(koji.config)
        session = koji.ClientSession(koji.config.server, session_opts)
        _KOJI_SESSION = (session, koji)
    return _KOJI_SESSION

def koji_builds_exist(tag, package, opts):
    session, _ = koji_session(opts)

    print(f'Checking for {package} in tag {tag}...', end=' ')
    tagged = session.listTagged(tag, latest=True, inherit=False, package=package)
    print(tagged[0]['nvr'] if tagged else '(no)')
    return bool(tagged)

def bodhi_builds_exist(branch, package, opts):
    releases = requests.get(BODHI_RELEASES).json()['releases']

    for entry in releases:
        if entry['branch'] == branch:
            tags = [v for k,v in entry.items() if k.endswith('_tag') and v]
            print(f'Found branch {branch} in bodhi with tags:', ', '.join(tags))
            for tag in tags:
                if koji_builds_exist(tag, package, opts):
                    return True

            print(f'No builds found in koji for branch {branch}')
            return False

    print(f'Branch {branch} not found in bodhi, checking if branch matches pattern...')
    m = re.match(NORMAL_BRANCHES, branch)
    if m:
        print('...it does, do not delete')
        return True
    print('...no match, seems OK to remove')
    return False

def find_hash(build):
    return build['source'].rsplit('#', 1)[1]

def list_builds(package, opts):
    session, koji = koji_session(opts)

    try:
        pkg = session.getPackageID(package, strict=True)
    except koji.GenericError as e:
        if 'Invalid package name' in str(e):
            return {}
        else:
            raise
    builds = session.listBuilds(packageID=pkg, state=koji.BUILD_STATES['COMPLETE'])

    with session.multicall(strict=True) as msession:
        for build in builds:
            if build['source'] is None:
                build['source'] = msession.getTaskInfo(build['task_id'], request=True)
    for build in builds:
        if isinstance(build['source'], koji.VirtualCall):
            r = build['source'].result
            if r is None:
                # This seems to happen for very old builds, e.g. buildbot-0.7.5-1.fc7.
                build['source'] = None
                nvr, time = build['nvr'], build['creation_time']
                print(f'Warning: build {nvr} from {time} has no source, ignoring.')
            else:
                build['source'] = r['request'][0]

    by_hash = {find_hash(b):b for b in builds if b['source']}
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


def rpm_eval(expression, macros):
    cmd = ['rpm']
    for macro, value in macros.items():
        cmd.append('--define')
        cmd.append(f'{macro} {value}')
    cmd.append('--eval')
    cmd.append(expression)
    return subprocess.check_output(cmd, text=True).strip()


def name_in_spec_file(commit, package):
    try:
        spec = (commit.tree / f'{package}.spec').data
    except KeyError:
        print(f"Commit {commit.hex} doesn't have '{package}.spec', looking for other specs.")
        specs = set()
        for candidate in commit.tree:
            if candidate.name.endswith(".spec"):
                specs.add(candidate)
                print(f"Found '{candidate.name}'.")
        if not specs:
            print(f"Commit {commit.hex} doesn't have '*.spec', assuming package is unbuildable.")
            return None
        if len(specs) > 1:
            msg = f"Commit {commit.hex} has multiple '*.spec' files, aborting."
            raise NotImplementedError(msg)
        spec = specs.pop().data

    # We don't try to decode the whole spec file here, to reduce the chances of trouble.
    # Just any interesting lines.
    macros = {}
    for line in spec.splitlines():
        try:
            if line.startswith(b'Name:'):
                name = line[5:].decode().strip()
                return rpm_eval(name, macros)

            macro_def = MACRO_DEF_RE.match(line)
            if macro_def:
                macros[macro_def.group('macro').decode()] = macro_def.group('value').decode()
        except UnicodeDecodeError:
            print(f"Something is wrong: commit {commit.hex} has busted encoding'.")
            raise

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
        branch_name = branch.branch_name
        local = True
    except KeyError:
        branch = repo.branches.remote[opts.branch]
        l = len(branch.remote_name)
        branch_name = branch.branch_name[l+1:]
        local = False

    if branch_name == 'master':
        print("Branch 'master' cannot be deleted.")
        return 1

    if bodhi_builds_exist(branch_name, opts.package, opts):
        print('Branch was used to build packages, cannot delete.')
        return 1

    other = list(containing_branches(repo, branch.target, local=local, ignore_branch=branch))
    if other:
        names = ', '.join(o.name for o in other)
        print(f'Branch merged into {names}. Safe to delete.')
        return 0

    print('Branch has commits not found anywhere else. Looking for builds.')
    builds = {opts.package: list_builds(opts.package, opts)}

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
        if real_name is not None and real_name not in builds:
            print(f"{commit.hex} has Name: {real_name}. Looking for builds.")
            builds[real_name] = list_builds(real_name, opts)

        for name in builds:
            built = builds[name].get(commit.hex, None)
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
