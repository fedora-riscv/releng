#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier:      GPL-2.0
# Author: Mohan Boddu <mboddu@bhujji.com>
#
# Private compose from a tag using odcs
#

import argparse
from odcs.client.odcs import ODCS, AuthMech, ComposeSourceTag

# We need oidc token to authenticate to odcs and a koji tag to compose from
parser = argparse.ArgumentParser()
parser.add_argument("token", help="OIDC token for authenticating to ODCS")
parser.add_argument("tag", help="koji tag to compose")
args = parser.parse_args()
token = args.token
tag = args.tag

odcs = ODCS("https://odcs.fedoraproject.org",
            auth_mech=AuthMech.OpenIDC,
            openidc_token=token)

source = ComposeSourceTag(tag)

# Making a private compose with no inheritance
compose = odcs.request_compose(source, target_dir="private", flags=["no_inheritance"])
print(compose)
