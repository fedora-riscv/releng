#!/usr/bin/python

"""
Simple small CLI utility to list who maintains/watches what on dist-git.

It can works from either one or more username specified as CLI argument
or retrieve this list of usernames from a file that has one username per
line.

It can be tweaked to report only packages watched, or maintained, or both
(which is the default).

"""

import argparse
import collections
import logging
import os
import sys

import requests

_log = logging.getLogger(__name__)
dist_git_base = "https://src.fedoraproject.org"


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
        "maintain or watch in dist-git."
    )
    parser.add_argument(
        dest="usernames", nargs="*", help="Names of the users to check.",
    )
    parser.add_argument(
        "--from-file",
        dest="users_file",
        help="Path to a file containing the users to check (one per line).",
    )
    report_group = parser.add_mutually_exclusive_group()
    report_group.add_argument(
        "--watch",
        action="store_const",
        dest="report",
        const="watch",
        default="all",
        help="Only report watched projects",
    )
    report_group.add_argument(
        "--maintain",
        action="store_const",
        dest="report",
        const="maintain",
        help="Only report maintained projects",
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


def is_maintainer(username, namespace_name):
    """ Returns whether the specified username is listed in the maintainers
    list of the specified package. """
    req = requests.get(f"{dist_git_base}/api/0/{namespace_name}")
    project = req.json()
    maintainers = set([project["user"]["name"]])
    for acl in project["access_users"]:
        maintainers.update(set(project["access_users"][acl]))

    return username in maintainers


def main(args):
    """ For the specified list of users, retrieve what they are maintaining
    or watching in dist-git."""

    args = get_arguments(args)
    setup_logging(log_level=args.log_level)
    _log.debug("Log level set to: %s", args.log_level)

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
    req = requests.get(f"{dist_git_base}/extras/pagure_bz.json")
    pagure_bz = req.json()

    packages_per_user = collections.defaultdict(list)
    for namespace in pagure_bz:
        for package in pagure_bz[namespace]:
            _log.debug("Processing %s/%s", namespace, package)
            for user in pagure_bz[namespace][package]:
                if user in usernames:
                    packages_per_user[user].append(f"{namespace}/{package}")

    for username in sorted(usernames):
        _log.debug("Processing: %s", username)
        for pkg in sorted(packages_per_user[username]):
            if is_maintainer(username, pkg):
                if args.report in ["all", "maintain"]:
                    print(f"{username} is maintaining {pkg}")
            else:
                if args.report in ["all", "watch"]:
                    print(f"{username} is watching {pkg}")
        print()


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        pass
