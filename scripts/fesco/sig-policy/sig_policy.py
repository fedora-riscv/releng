#!/usr/bin/python3

# sig_policy.py
# =============
#
# This script enacts the FESCo SIG Policy as documented here:
# https://docs.fedoraproject.org/en-US/fesco/SIG_policy/
#
# Author: Fabio Valentini <decathorpe@gmail.org>
# SPDX-License-Identifier: Unlicense

import argparse
import functools
import os
import sys

import fedrq.config
import requests
from fedrq.backends.base import RepoqueryBase

# (namespace, name of SIG group, ACL, package name filter)
POLICY = [
    # Go SIG: https://pagure.io/fesco/fesco-docs/pull-request/68
    ("rpms", "go-sig", "commit", lambda x: x in go_packages()),
    # R SIG: https://pagure.io/fesco/fesco-docs/pull-request/69
    ("rpms", "r-maint-sig", "commit", lambda x: x.startswith("R-") or x in r_packages()),
    # Rust SIG: https://pagure.io/fesco/fesco-docs/pull-request/66
    ("rpms", "rust-sig", "commit", lambda x: x.startswith("rust-")),
]

PAGURE_DIST_GIT_DATA_URL = "https://src.fedoraproject.org/extras/pagure_bz.json"

VALID_ACLS = ["ticket", "commit", "admin"]


@functools.cache
def get_rq() -> RepoqueryBase:
    """
    Return a RepoqueryBase object with the rawhide buildroot repositories
    """
    return fedrq.config.get_config().get_rq("rawhide", "@buildroot")


@functools.cache
def go_packages() -> set[str]:
    rq = get_rq()
    query = rq.query(
            requires=rq.query(name=["golang", "golang-bin", "go-rpm-macros"]),
            # Only BuildRequires are covered by the policy
            arch="src",
    )
    packages = {package.name for package in query}
    return packages


@functools.cache
def r_packages() -> set[str]:
    rq = get_rq()
    query = rq.query(
        requires__glob="libR.so*",
        # Only Requires are covered by the policy
        arch__neq="src",
    )
    packages = {package.source_name for package in query}

    # add "R" which does not link with "libR.so" itself
    packages.add("R")

    return packages


def get_package_data() -> dict[str, list[str]]:
    """
    Download the latest cached mapping from source package name -> list of
    (co)maintainers from pagure-dist-git.

    Raises an exception if the HTTP GET request failed, or if the data is not
    valid JSON in the expected format.
    """

    ret = requests.get(PAGURE_DIST_GIT_DATA_URL)
    ret.raise_for_status()

    data = ret.json()

    return data


def add_package_acl(namespace: str, package: str, group: str, acl: str, token: str):
    """
    Send an HTTP POST request to the pagure API endpoint for modifying ACLs on
    a project.

    Raises an exception if an HTTP error status was returned, or if the network
    request failed for other reasons.
    """

    if acl not in VALID_ACLS:
        raise ValueError(f"Not a valid ACL: {acl}")

    url = f"https://src.fedoraproject.org/api/0/{namespace}/{package}/git/modifyacls"

    payload = {
        "user_type": "group",
        "name": group,
        "acl": acl,
    }

    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.post(url, data=payload, headers=headers)
    response.raise_for_status()


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument(
        "--dry-run",
        "-n",
        dest="dry",
        action="store_true",
        help="print results but do not modify any data",
    )
    cli.add_argument(
        "--api-token",
        dest="token",
        action="store",
        default=None,
        help="API token for src.fedoraproject.org (overrides PAGURE_API_TOKEN)",
    )
    args = cli.parse_args()

    token = args.token or os.environ.get("PAGURE_API_TOKEN")
    if not token:
        print("PAGURE_API_TOKEN environment variable not set.", file=sys.stderr)
        return 1

    try:
        package_data = get_package_data()

    except IOError as ex:
        print("Failed to fetch data from pagure-dist-git:", file=sys.stderr)
        print(ex, file=sys.stderr)
        return 1

    # keep track of failed requests
    failures = dict()

    for (namespace, group, acl, filtr) in POLICY:
        print(f"Processing group: {group}")

        packages = package_data[namespace]

        # keep track of candidate packages
        candidates = []

        for (package, maintainers) in packages.items():
            # check if the package matches the filter set by the policy
            if not filtr(package):
                continue

            # check if the package is already retired on all branches
            if maintainers == ["orphan"]:
                continue

            # check if the package already has the group as co-maintainer
            # FIXME: this cannot check whether the ACL is present but too low
            if f"@{group}" not in maintainers:
                candidates.append(package)

        if not candidates:
            print(f"No pending actions for group {group!r}.")
            print()
            continue

        # keep track of failed requests
        failed = []

        for candidate in candidates:
            print(f"- add {group!r} with {acl!r} ACL to '{namespace}/{candidate}'")

            if not args.dry:
                try:
                    add_package_acl(namespace, candidate, group, acl, token)
                except Exception as ex:
                    print(ex, file=sys.stderr)
                    failed.append(candidate)

        if failed:
            failures[group] = failed

        print()

    if not failures:
        print("Finished successfully.")
        return 0

    print("Finished with errors:")
    for (group, failed) in failures:
        for package in failed:
            print(f"- failed to add {group!r} group to package {package!r}")

    return 1


if __name__ == "__main__":
    try:
        exit(main())

    except KeyboardInterrupt:
        print("Cancelled.")
        exit(0)

    except Exception as e:
        print(e, file=sys.stderr)
        exit(1)

