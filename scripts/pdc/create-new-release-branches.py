""" create-new-release-branches.py - Add new Fedora release branch for every
active component in PDC.

You can run this on pdc-backend01, the token is in /etc/pdc.d/
You can also find the token in the private git repo.
"""
from __future__ import print_function
import os
import re
from datetime import datetime, date
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
parser.add_argument('branch', help='Name of the release branch (f27)')
parser.add_argument('namespace', help='Name of the namespace (rpm or module)')
parser.add_argument('eol', help='End of life date for the release, in the '
                                'format of "2020-01-01"')
parser.add_argument('--createfile', action='store_true', default=False,
                    help='Creates an output file with all the components that '
                         'were modified')
args = parser.parse_args()


if __name__ == '__main__':
    if not re.match(r'^f\d\d$', args.branch):
        utilities.die('The branch "{0}" is not a release branch'.format(
            args.branch))

    if not re.match(r'^\d{4}-\d{2}-\d{2}', args.eol):
        utilities.die('The EOL of "{0}" is not in a valid format'.format(
            args.eol))

    today = date.today()
    eol = datetime.strptime(args.eol, '%Y-%m-%d').date()
    if eol < today:
        utilities.die('The EOL of "{0}" is already expired'.format(args.eol))

    print("Connecting to PDC args.server %r with token %r" % (args.servername, args.token))
    pdc = pdc_client.PDCClient(args.servername, token=args.token)

    slas = ['security_fixes', 'bug_fixes']
    utilities.verify_slas(pdc, slas)

    active_components = set()
    for branch in pdc.get_paged(res=pdc['component-branches/'],
                                name='master', active=True, type=args.namespace, page_size=100):
        package = branch['global_component']
        package_type = branch['type']
        critpath = branch['critical_path']
        # Skip the Rust packages
        # https://pagure.io/fesco/issue/2068
        if (package.startswith('rust-') and package not in {'rust-srpm-macros', 'rust-packaging'})
             or package in {'zola', 'stratisd'}:
            continue
        active_components.add(
            '%s/%s' % (package_type, package))
        print('Ensuring {0}/{1}#{2} exists'.format(
            package_type, package, args.branch))
        utilities.ensure_component_branches(
            pdc, package, slas, args.eol, args.branch,
            package_type, critpath=critpath, force=True)

    if args.createfile:
        components_txt = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'components.txt'))
        print('Generating {0}'.format(components_txt))
        with open(components_txt, 'w') as components_txt_stream:
            components_txt_stream.write('\n'.join(active_components))

    print('All done!')
