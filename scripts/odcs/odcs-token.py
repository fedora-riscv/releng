#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier:      GPL-2.0
# Author: Mohan Boddu <mboddu@bhujji.com>
#
# Private compose from a tag using odcs
#

"""

Usage: python odcs-token.py

This is used to generate a token needed to run odcs composes 

"""

import openidc_client
staging = False

if staging:
    id_provider = 'https://id.stg.fedoraproject.org/openidc/'
else:
    id_provider = 'https://id.fedoraproject.org/openidc/'

# Get the auth token using the OpenID client.
oidc = openidc_client.OpenIDCClient(
    'odcs',
    id_provider,
    {'Token': 'Token', 'Authorization': 'Authorization'},
    'odcs-authorizer',
    'notsecret',
)

scopes = [
    'openid',
    'https://id.fedoraproject.org/scope/groups',
    'https://pagure.io/odcs/new-compose',
    'https://pagure.io/odcs/renew-compose',
    'https://pagure.io/odcs/delete-compose',
]
try:
    token = oidc.get_token(scopes, new_token=True)
    token = oidc.report_token_issue()
    print(token)
except requests.exceptions.HTTPError as e:
    print(e.response.text)
    raise
