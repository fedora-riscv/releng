#!/usr/bin/python3
"""
This is used to adjust EOL of list of modules
and their branches in the same order with a date.

Usage:
    python adjust-eol-modules.py fedora *token* module --modules mod1 mod2 --branches 1.10 2.10 --eol 2018-12-01

https://pdc.fedoraproject.org/rest_api/v1/component-branches/

Note that branches must be associated with SLAs and EOLs.

You can run this on pdc-backend01, the token is in /etc/pdc.d/
You can also find the token in the private git repo.
"""

import argparse

try:
    import utilities
except ImportError:
    print("Try setting PYTHONPATH to find the utilities.py file.")
    raise

import pdc_client

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('servername', help='PDC server name.  See /etc/pdc.d/')
parser.add_argument('token', help='PDC token for authentication.')
parser.add_argument('type', help='Type of the package (rpm, module, container, ..)')
parser.add_argument('-y', '--yes', dest='yes', action='store_true',
                    default=False,
                    help='Force "yes" to every question.')
parser.add_argument('--modules', nargs="+", help='Name of the modules')
parser.add_argument('--branches', nargs="+", help='Name of the branches (f26, or 1.12, or master)')
parser.add_argument('--eol', nargs="+", help='End of life date for the SLAs, '
                    'in the format of "2020-01-01".')

args = parser.parse_args()


if __name__ == '__main__':
    print("Connecting to PDC args.server %r with token %r" % (args.servername, args.token))
    pdc = pdc_client.PDCClient(args.servername, token=args.token)
    if len(args.eol) == 1:
        for idx, module in enumerate(args.modules):
            utilities.patch_eol(
                pdc, module, args.eol[0], args.branches[idx], args.type, args.yes)
    else:
        for idx, module in enumerate(args.modules):
            utilities.patch_eol(
                pdc, module, args.eol[idx], args.branches[idx], args.type, args.yes)
