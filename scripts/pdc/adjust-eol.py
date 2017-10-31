#!/usr/bin/python3
""" adjust-eol.py - Modify the EOL on an existing SL, on an existing branch.

Adjust EOLs with care.  Read the SOP first for policy.

https://pdc.fedoraproject.org/rest_api/v1/component-branches/

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
parser.add_argument('package', help='Name of the package')
parser.add_argument('type', help='Type of the package (rpm, module, container, ..)')
parser.add_argument('branch', help='Name of the branch (f26, or 1.12, or master)')
parser.add_argument('eol', help='End of life date for the SLAs, '
                    'in the format of "2020-01-01".  May also be "default".')
parser.add_argument('-y', '--yes', dest='yes', action='store_true',
                    default=False,
                    help='Force "yes" to every question.')

args = parser.parse_args()


if __name__ == '__main__':
    print("Connecting to PDC args.server %r with token %r" % (args.servername, args.token))
    pdc = pdc_client.PDCClient(args.servername, token=args.token)

    utilities.patch_eol(
        pdc, args.package, args.eol, args.branch, args.type, args.yes)
