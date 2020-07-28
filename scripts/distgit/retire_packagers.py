#!/usr/bin/python3

"""
This script queries dist-git for all the packages a given packager maintains,
has commit or watches.
Package that the packager is the main admin are then orphaned. The packager is
then removed from all packages that they have commit for and their watch status
is reset on every packages that they are watching.

"""

import argparse
import collections
import logging
import os
import sys

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

_log = logging.getLogger(__name__)
dist_git_base = "https://src.fedoraproject.org"
pagure_token = None


def retry_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def setup_logging(log_level: int):
    handlers = []

    _log.setLevel(log_level)
    # We want all messages logged at level INFO or lower to be printed to stdout
    info_handler = logging.StreamHandler(stream=sys.stdout)
    handlers.append(info_handler)

    if log_level == logging.INFO:
        # In normal operation, don't decorate messages
        for handler in handlers:
            handler.setFormatter(logging.Formatter("%(message)s"))

    logging.basicConfig(level=log_level, handlers=handlers)


def get_arguments(args):
    """ Load and parse the CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Looks for the specified list of users what they "
        "maintain or watch in dist-git.\nIf --retire is specified, all the ACL "
        "the packager(s) have in dist-git will be removed. If they are main admins "
        "of some packages, these packages will be orphaned. If they have commit "
        "access on some packages, they will no longer have these access. If they "
        "watch a package, their watch status will be reset. Note: the source of "
        "information is refreshed hourly, so if you run the script twice with "
        "`--retire` you may not see a difference here."
    )
    parser.add_argument(
        dest="usernames", nargs="*", help="Names of the users to retire.",
    )
    parser.add_argument(
        "--from-file",
        dest="users_file",
        help="Path to a file containing the users to check (one per line).",
    )
    parser.add_argument(
        "--retire",
        action="store_true",
        default=False,
        help="Retire the user(s) (ie: orphan, remove from ACL, reset watch)",
    )
    parser.add_argument(
        "--api-token",
        dest="pagure_token",
        default=os.environ.get("PAGURE_TOKEN"),
        help="Pagure token to use to interact with dist-git. It can also be set "
        "via the PAGURE_TOKEN environment variable. (This script requires the "
        "`modifyproject` ACL to work)",
    )
    report_group = parser.add_mutually_exclusive_group()
    report_group.add_argument(
        "--watch",
        action="store_const",
        dest="report",
        const="watch",
        default="all",
        help="Only report/act on watched projects",
    )
    report_group.add_argument(
        "--maintain",
        action="store_const",
        dest="report",
        const="maintain",
        help="Only report/act projects the packagers have commit access to",
    )

    log_level_group = parser.add_mutually_exclusive_group()
    log_level_group.add_argument(
        "--debug",
        action="store_const",
        dest="log_level",
        const=logging.DEBUG,
        default=logging.INFO,
        help="Enable debugging output",
    )

    return parser.parse_args(args)


def user_access(session, username, namespace_name):
    """ Returns whether the specified username is listed in the maintainers
    list of the specified package. """
    req = session.get(f"{dist_git_base}/api/0/{namespace_name}")
    project = req.json()
    level = None
    if username == project["user"]["name"]:
        level = "main admin"
    else:
        maintainers = set()
        for acl in project["access_users"]:
            maintainers.update(set(project["access_users"][acl]))

        if username in maintainers:
            level = "maintainer"

    return level


def unwatch_package(namespace, name, username):
    """ Reset the watch status of the given user on the specified project. """
    _log.debug("Going to reset watch status of %s on %s/%s", username, namespace, name)
    base_url = dist_git_base.rstrip("/")
    session = retry_session()

    # Reset the watching status
    url = f"{base_url}/api/0/{namespace}/{name}/watchers/update"
    headers = {"Authorization": f"token {pagure_token}"}
    data = {"status": -1, "watcher": username}

    req = session.post(url, data=data, headers=headers)
    if not req.ok:
        print("**** REQUEST FAILED")
        print("  - Unwatch package")
        print(req.url)
        print(data)
        print(headers)
        print(req.text)
    else:
        print(f"  {username} is no longer watching {namespace}/{name}")
    session.close()


def orphan_package(namespace, name, username):
    """ Give the specified project on dist_git to the ``orphan`` user.
    """
    _log.debug("Going to orphan: %s/%s from %s", namespace, name, username)
    base_url = dist_git_base.rstrip("/")
    session = retry_session()

    # Orphan the package
    url = f"{base_url}/api/0/{namespace}/{name}"
    headers = {"Authorization": f"token {pagure_token}"}
    data = {"main_admin": "orphan", "retain_access": False}

    req = session.patch(url, data=data, headers=headers)
    if not req.ok:
        print("**** REQUEST FAILED")
        print("  - Orphan package")
        print(req.url)
        print(data)
        print(req.text)
    else:
        print(f"  {username} is no longer the main admin of {namespace}/{name}")
    session.close()

    unwatch_package(namespace, name, username)


def remove_access(namespace, name, username, usertype):
    """ Remove the ACL of the specified user/group on the specified project. """
    _log.debug("Going to remove %s from %s/%s", username, namespace, name)
    base_url = dist_git_base.rstrip("/")
    session = retry_session()

    # Remove ACL on the package
    url = f"{base_url}/{namespace}/{name}/git/modifyacls"
    headers = {"Authorization": f"token {pagure_token}"}
    data = {
        "user_type": usertype,
        "name": username,
    }

    req = session.patch(url, data=data, headers=headers)
    if not req.ok:
        print("**** REQUEST FAILED")
        print("  - Remove ACL")
        print(req.url)
        print(data)
        print(req.text)
    else:
        print(f"  {username} is no longer maintaining {namespace}/{name}")
    session.close()

    if usertype == "user":
        # Reset the watching status
        unwatch_package(namespace, name, username)


def main(args):
    """ For the specified list of users, retrieve what they are maintaining
    or watching in dist-git."""

    args = get_arguments(args)
    setup_logging(log_level=args.log_level)
    _log.debug("Log level set to: %s", args.log_level)

    if args.pagure_token:
        global pagure_token
        pagure_token = args.pagure_token

    if not pagure_token and args.retire:
        print(
            "No pagure token set in the CLI argument or via the PAGURE_TOKEN "
            "environment variable. Going to ignore --retire"
        )
        args.retire = False

    usernames = []
    if args.users_file:
        _log.debug("Loading usernames for file: %s", args.users_file)
        if not os.path.exists(args.users_file):
            _log.info("No such file found: %s", args.users_file)
        try:
            with open(args.users_file) as stream:
                usernames = [l.strip() for l in stream.readlines()]
        except Exception as err:
            _log.debug(
                "Failed to load/read the file: %s, error is: %s", args.users_file, err
            )
    else:
        _log.debug("Loading usernames for the CLI arguments")
        usernames = args.usernames

    _log.debug("Loading info from dist-git's pagure_bz.json file")
    session = retry_session()
    req = session.get(f"{dist_git_base}/extras/pagure_bz.json")
    pagure_bz = req.json()
    session.close()

    packages_per_user = collections.defaultdict(list)
    for namespace in pagure_bz:
        for package in pagure_bz[namespace]:
            _log.debug("Processing %s/%s", namespace, package)
            for user in pagure_bz[namespace][package]:
                if user in usernames:
                    packages_per_user[user].append(f"{namespace}/{package}")

    for username in sorted(usernames):
        _log.debug("Processing user: %s", username)
        for pkg in sorted(packages_per_user[username]):
            level = user_access(session, username, pkg)
            if level:
                if args.report in ["all", "maintain"]:
                    print(f"{username} is {level} of {pkg}")
                    if args.retire:
                        namespace, name = pkg.split("/", 1)
                        if level == "main admin":
                            orphan_package(namespace, name, username)
                        elif level == "maintainer":
                            remove_access(namespace, name, username, "user")

            else:
                if args.report in ["all", "watch"]:
                    print(f"{username} is watching {pkg}")
                    if args.retire:
                        namespace, name = pkg.split("/", 1)
                        unwatch_package(namespace, name, username)
        print()


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        pass
