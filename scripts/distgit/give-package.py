#! /usr/bin/python -tt
""" Give a package in pagure-on-dist-git from one user to another.

This can also be used to give the package to the 'orphan' user.

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
import sys

try:
    import utilities
except ImportError:
    print("Try setting PYTHONPATH to find the utilities.py file.")
    raise

PAGURE_URL = 'https://src.fedoraproject.org/api/0/'


def main():
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("package", help="The package that should be given.")
    parser.add_argument("custodian", help="The user taking over the package.")
    args = parser.parse_args()
    session = utilities.retry_session()
    try:
        namespace, package = args.package.split('/')
    except:
        print("Package must be like <namespace>/<name>, not %r" % args.package)
        sys.exit(1)

    utilities.give_package(session, namespace, package, args.custodian)


if __name__ == "__main__":
    main()
