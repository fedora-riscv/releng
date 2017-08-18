#! /usr/bin/python -tt
""" Orphan all packages of a given set of users.

If there are other committers on a package, the first one is promoted to be the
new owner.

If there are no other committers, then the package is given to the `orphan`
user.

You need a privileged pagure token in /etc/fedrepo_req/config.ini

    [admin]
    pagure_api_token = something secret

You can generate such a token on pkgs02 with:

    $ PAGURE_CONFIG=/etc/pagure/pagure.cfg pagure-admin admin-token --help
"""
# Copyright (c) 2017 Red Hat
# SPDX-License-Identifier:	GPL-2.0
#
# Authors:
#     Ralph Bean <rbean@redhat.com>

import argparse

try:
    import utilities
except ImportError:
    print("Try setting PYTHONPATH to find the utilities.py file.")
    raise


PAGURE_URL = 'https://src.fedoraproject.org/api/0/'


def get_all_packages_for_user(session, user):
    url = PAGURE_URL + 'projects'
    params = dict(owner=user, fork=False)
    response = session.get(url, params=params, timeout=400)
    if not bool(response):
        raise IOError("Failed GET %r %r" % (response.request.url, response))
    for project in response.json()['projects']:
        yield project


def triage_packages(packages, user):
    for package in packages:
        for kind in ('admin', 'commit'):
            others = package['access_users'][kind]
            try:
                others.remove(user)
            except ValueError:
                # Owner doesn't have commit.  Weird, but ok.
                pass
            if others:
                # Select the first one to become the new owner.
                yield package, sorted(others)[0]
                break
        else:
            yield package, 'orphan'


def main():
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("users", nargs="*",
                        help="Users to remove.")
    args = parser.parse_args()

    session = utilities.retry_session()
    for user in args.users:
        print("Investigating packages for user %r" % user)
        packages = get_all_packages_for_user(session, user)
        transfers = triage_packages(packages, user)

        # Exhaust the generator
        transfers = list(transfers)

        for package, custodian in transfers:
            print("%s/%s will be given to %s" % (
                package['namespace'], package['name'], custodian))

        response = raw_input("Is this okay? [y/N]")
        if response.lower() not in ('y', 'yes'):
            print("!! OK.  Bailing out for %r" % user)
            continue

        print("Starting transfers")
        for package, custodian in transfers:
            utilities.give_package(session, package, custodian)


if __name__ == "__main__":
    main()
