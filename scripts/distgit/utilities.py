#! /usr/bin/python -tt
""" Utilities for manipulating dist-git (pagure). """
# Copyright (c) 2017 Red Hat
# SPDX-License-Identifier:	GPL-2.0
#
# Authors:
#     Ralph Bean <rbean@redhat.com>

import pprint
import sys
import traceback

import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

try:
    from fedrepo_req.pagure import get_pagure_auth_header
    admin_headers = get_pagure_auth_header('admin', token_type='global')
except:
    traceback.print_exc()
    print("Failed to load admin tokens from fedrepo-req-admin")
    sys.exit(1)

PAGURE_URL = 'https://src.fedoraproject.org/api/0/'


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
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def give_package(session, namespace, package, custodian):
    print("Giving %s/%s to %s" % (
        namespace, package, custodian))

    url = PAGURE_URL + namespace + '/' + package
    payload = {'main_admin': custodian}
    response = session.patch(
        url,
        data=payload,
        headers=admin_headers,
        timeout=60,
    )
    if not bool(response):
        try:
            pprint.pprint(response.json())
        except:
            pass
        raise IOError("Failed PATCH %r %r" % (response.request.url, response))
