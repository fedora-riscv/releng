""" insert-sla.py - Add a new branch SLA to PDC.

https://pdc.fedoraproject.org/rest_api/v1/component-sla-types/

Branches in dist-git may have arbitrary EOLs and SLAs, but the SLAs must be
chosen from a set specified by release-engineering.

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
parser.add_argument('slas', help='Comma-separated list of SLAs.')
parser.add_argument('eol', help='End of life date for the SLAs, '
                    'in the format of "2020-01-01"')
parser.add_argument('-y', '--yes', dest='yes', action='store_true',
                    default=False,
                    help='Force "yes" to every question.')

args = parser.parse_args()


if __name__ == '__main__':
    print("Connecting to PDC args.server %r with token %r" % (args.servername, args.token))
    pdc = pdc_client.PDCClient(args.servername, token=args.token)

    slas = args.slas.split(',')

    utilities.verify_slas(
        pdc, slas)
    utilities.ensure_global_component(
        pdc, args.package, args.yes)
    utilities.ensure_component_branches(
        pdc, args.package, slas, args.eol, args.branch, args.type, args.yes)
