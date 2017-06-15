""" sync-branches-from-pkgdb.py

This script is a one-off, to synchronize all our collections and branches from
pkgdb into the new-world of PDC+pagure.  You probably will never need to run
it... but it is saved here for posterity.

https://fedoraproject.org/wiki/Changes/ArbitraryBranching

This script takes *forever* to run.

You can run this on pdc-backend01, the token is in /etc/pdc.d/
You can also find the token in the private git repo.
"""

from __future__ import print_function

import argparse
import json
import os
import time

import requests

try:
    import utilities
except ImportError:
    print("Try setting PYTHONPATH to find the utilities.py file.")
    raise

import pdc_client

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('servername', help='PDC server name.  See /etc/pdc.d/')
parser.add_argument('token', help='PDC token for authentication.')
args = parser.parse_args()


# These are old, and I don't know what to do with them.  When was their EOL?
ignored_branches = [
    'RHL-9',
    'RHL-8',

    'OLPC-2',
    'OLPC-4',
    'olpc3',
]


def _pkgdb_data_by_page(page):
    """ Returns an export of pkgdb's data. """

    cache_file = '/var/tmp/pkgdb-export-page-%i.cache' % page
    if os.path.exists(cache_file):
        print("Using cache of pkgdb data in %r.  Delete it to re-pull." % cache_file)
        with open(cache_file, 'r') as f:
            return json.loads(f.read())

    url = 'https://admin.fedoraproject.org/pkgdb/api/packages/?acls=True&limit=5&page=%i' % page
    print("  Querying %r" % url, end='...')
    start = time.time()
    response = requests.get(url)
    print("  Query took %r seconds" % (time.time() - start))
    data = response.json()

    print("Writing cache of pkgdb information to %r" % cache_file)
    with open(cache_file, 'w') as f:
        f.write(json.dumps(data))
    return data

def pkgdb_data():
    initial = 0
    for page in range(initial, _pkgdb_data_by_page(initial)['page_total']):
        data = _pkgdb_data_by_page(page)
        for entry in data['packages']:
            yield entry

def get_implicit_slas(branchname):
    standard = [
        'bug_fixes',
        'security_fixes',
    ]
    lookup = {
        'master': ['rawhide'],
        'f26': standard,
        'f25': standard,
        'f24': standard,
        'f23': standard,
        'f22': standard,
        'f21': standard,
        'f20': standard,
        'f19': standard,
        'f18': standard,
        'f17': standard,
        'f16': standard,
        'f15': standard,
        'f14': standard,
        'f13': standard,
        'f12': standard,
        'f11': standard,
        'f10': standard,
        'f9': standard,
        'f8': standard,
        'f7': standard,
        'fc6': standard,
        'FC-6': standard,
        'FC-5': standard,
        'FC-4': standard,
        'FC-3': standard,
        'FC-2': standard,
        'FC-1': standard,

        'epel7': standard + ['stable_api'],
        'el6': standard + ['stable_api'],
        'el5': standard + ['stable_api'],
        'el4': standard + ['stable_api'],
    }
    return lookup[branchname]

def get_implicit_eol(branchname):
    lookup = {
        'master': '2222-01-01',  # THE FUTURE!
        'f26': '2018-07-01',
        'f25': '2017-12-01',
        'f24': '2017-08-11',
        'f23': '2016-12-20',
        'f22': '2016-07-19',
        'f21': '2015-12-01',
        'f20': '2015-06-23',
        'f19': '2015-01-06',
        'f18': '2014-01-14',
        'f17': '2013-07-30',
        'f16': '2013-02-12',
        'f15': '2012-06-26',
        'f14': '2011-12-09',
        'f13': '2011-06-24',
        'f12': '2010-12-02',
        'f11': '2010-06-25',
        'f10': '2009-12-17',
        'f9': '2009-07-10',
        'f8': '2009-01-07',
        'f7': '2008-06-13',
        'fc6': '2007-12-07',
        'FC-6': '2007-12-07',
        'FC-5': '2007-07-02',
        'FC-4': '2006-08-07',
        'FC-3': '2006-01-16',
        'FC-2': '2005-04-11',
        'FC-1': '2004-09-20',

        # https://access.redhat.com/support/policy/updates/errata
        'epel7': '2024-06-30',
        'el6': '2020-11-30',
        'el5': '2017-03-21',
        'el4': '2012-02-29',
        'el3': '2010-10-31',
    }
    return lookup[branchname]

def lookup_component_type(pkgdb_type):
    lookup = {
        'rpms': 'rpm',
        'modules': 'module',
        'containers': 'container',
    }
    return lookup[pkgdb_type]


if __name__ == '__main__':
    print("Connecting to PDC args.server %r with token %r" % (args.servername, args.token))
    pdc = pdc_client.PDCClient(args.servername, token=args.token)

    export = pkgdb_data()
    for entry in export:
        utilities.ensure_global_component(pdc, entry['name'], force=True)
        for acl in entry['acls']:
            # First, Ignore stuff that we don't know how to handle.
            if acl['collection']['branchname'] in ignored_branches:
                continue

            # Then, find our values for this pkgdb entry.
            slas = get_implicit_slas(acl['collection']['branchname'])
            eol = get_implicit_eol(acl['collection']['branchname'])
            branch_type = lookup_component_type(entry['namespace'])

            # Make sure everything is set in PDC.
            utilities.verify_slas(pdc, slas)
            utilities.ensure_component_branches(
                pdc,
                package=entry['name'],
                slas=slas,
                eol=eol,
                branch=acl['collection']['branchname'],
                type=branch_type,
                critpath=acl['critpath'],
                force=True,
            )
