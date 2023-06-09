#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier:      GPL-2.0
# Author: Mohan Boddu <mboddu@bhujji.com>
#
# Private compose from a tag using odcs
#

"""

Usage: python odcs-private-compose.py <token> <koji_tag> <sigkey>

This is used to generate private composes using ODCS.
This script is specifically used to generate openh264 repos.
The compsoe is stored in /srv/odcs/private/ dir on
odcs-backend-releng01.iad2.fedoraproject.org

"""

import argparse
from odcs.client.odcs import ODCS, AuthMech, ComposeSourceTag

# We need oidc token to authenticate to odcs and a koji tag to compose from
parser = argparse.ArgumentParser()
parser.add_argument("token", help="OIDC token for authenticating to ODCS")
parser.add_argument("tag", help="koji tag to compose")
parser.add_argument("sigkey", help="sigkey that was used to signed the builds in the tag")
args = parser.parse_args()
token = args.token
tag = args.tag
sigkey = args.sigkey

odcs = ODCS("https://odcs.fedoraproject.org",
            auth_mech=AuthMech.OpenIDC,
            openidc_token=token)

source = ComposeSourceTag(tag, sigkeys=[sigkey])

# Making a private compose with no inheritance
arches = ["armhfp", "i386", "x86_64", "aarch64", "ppc64le", "s390x"]
compose = odcs.request_compose(source, target_dir="private", arches = arches, flags=["no_inheritance"])
print(compose)
