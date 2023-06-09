# -*- coding: utf-8 -*-
# vi: ft=python
# Copyright (C) 2014 Red Hat Inc
# Copyright (C) 2014 Pierre-Yves Chibon, Chaoyi Zha, Toshio Kuratomi,
#                    Bill Nottingham
# Authors: Pierre-Yves Chibon <pingou@pingoured.fr>
#          Chaoyi Zha <summermontreal@gmail.com>
#          Bill Nottingham <notting@fedoraproject.org>
#          Toshio Kuratomi <toshio@fedoraproject.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
# See http://www.gnu.org/copyleft/gpl.html  for the full text of the
# license.
""" update_critpath - a commandline frontend for updating the critpath

Critpath updating SOP: https://docs.pagure.org/releng/sop_update_critpath.html

How to use:
 $ python update-critpath <critpath.txt> <branch>
for example
 $ python update-critpath critpath.txt f20
"""

from __future__ import print_function
import argparse
import json
import logging
import sys
import pdc_client
import dogpile.cache

# Here, 'fedora' is the name of the production instance, configured in
# /etc/pdc.d/.  See the PDC SOP for more information on authenticating.

# This is an on-disk cache to avoid hitting PDC over and over.
cache_filename = "/var/tmp/pdc-branch-cache.dbm"
def key_generator(ns, fn, **kw):
    return lambda **kwargs: "%r_%r|%r" % (ns, fn.__name__, json.dumps(kwargs))
cache = dogpile.cache.make_region(function_key_generator=key_generator)

# Initial simple logging stuff
logging.basicConfig()
LOG = logging.getLogger("update_critpath")


def setup_parser():
    '''
    Set up argparse
    '''
    parser = argparse.ArgumentParser(prog="update_critpath")
    # General connection options
    parser.add_argument('--debug', action='store_true',
                        help="Outputs bunches of debugging info")
    parser.add_argument('--test', action='store_true',
                        help="Uses the stg instance instead of the real pdc.")

    parser.add_argument(
        'branch', default='rawhide',
        help="Branch of the package to add to critpath (default: 'rawhide')")
    parser.add_argument(
        'txtlist',
        help="Filename containing list of packages to critpath")
    parser.add_argument(
        'token',
        help="PDC Token")

    return parser


def list_critpath(branch):
    ''' Return the set of packages flagged as critpatch in the specified
    branch.

    :arg branch: branch used to restrict the list of packages returned.
    :type branch: str
    :return: a set of package names with PDC branch IDs
    :rtype: set
    '''
    if not isinstance(branch, str):
        raise TypeError('branch *must* be a string')

    LOG.debug("Retrieving existing critpath list from PDC.")
    args = { 'name': branch, 'type': 'rpm', 'critical_path': True }
    results = pdc.get_paged(pdc['component-branches'], **args)

    pkgs = set()
    for result in results:
        pkgs.add("{id}:{global_component}".format(**result))
    LOG.debug("Done retrieving existing critpath list from PDC.")
    return pkgs


def prepend_pdc_branch_ids(global_components, branch):
    LOG.debug("Finding PDC branch IDs for supplied critpath list."
              "  (See cache in %s)" % cache_filename)
    pkgs = set()
    endpoint = pdc['component-branches']

    @cache.cache_on_arguments()
    def _get_pdc_branch_id(**args):
        results = list(pdc.get_paged(endpoint, **args))
        #critpath.py generates subpackages as well.
        #As there wont be any pdc entries for subpackages
        #we need to skip them
        if(len(results) == 1):
            return results[0]
        else:
            return None

    for i, component in enumerate(global_components):
        args = {'name': branch, 'type': 'rpm', 'global_component': component}
        result = _get_pdc_branch_id(**args)

        if result:
            pkgs.add("{id}:{global_component}".format(**result))
    LOG.debug("Done finding PDC branch IDs for supplied critpath list.")
    return pkgs


def update_critpath(current_critpath, new_critpath, branch):
    ''' Change critpath status of packages in PDC

    :arg current_critpath: a set listing all the packages that currently have
        the critpath package
    '''

    # Remove the critpath flag from packages which do not have it, but should.
    new_no = current_critpath - new_critpath
    LOG.debug('%i packages need critpath removed.' % len(new_no))
    for item in new_no:
        idx, name = item.split(':', 1)
        LOG.debug('  Sending PATCH for %s, (idx: %s)' % (name, idx))
        pdc['component-branches'][idx + '/'] += dict(critical_path=False)

    # Add the critpath flag to packages which should have it, but do not.
    new_yes = new_critpath - current_critpath
    LOG.debug('%i packages need critpath added.' % len(new_yes))
    for item in new_yes:
        idx, name = item.split(':', 1)
        LOG.debug('  Sending PATCH for %s, (idx: %s)' % (name, idx))
        pdc['component-branches'][idx + '/'] += dict(critical_path=True)


def main():
    ''' Main function '''
    # Set up parser for global args
    parser = setup_parser()
    # Parse the commandline
    try:
        arg = parser.parse_args()
    except argparse.ArgumentTypeError as err:
        print("\nError: {0}".format(err))
        return 2

    token = arg.token

    if arg.debug:
        LOG.setLevel(logging.DEBUG)

    if arg.test:
        global pdc
        LOG.info("Using staging environment")
        pdc = pdc_client.PDCClient('staging')
    else:
        pdc = pdc_client.PDCClient('fedora', token)



    LOG.debug("Using pdc branch cache %r" % cache_filename)
    cache.configure(
        "dogpile.cache.dbm",
        expiration_time=-1,  # Never!!
        arguments={"filename": cache_filename}
    )

    return_code = 0

    new_critpath = []
    LOG.debug("Reading supplied %r" % arg.txtlist)
    with open(arg.txtlist) as f:
        for line in f.readlines():
            new_critpath.append(line.strip())

    # At this point, the new_critpath list contains only package names.  We
    # need to enrich that with the IDs of the branch mappings from PDC
    new_critpath = prepend_pdc_branch_ids(new_critpath, arg.branch)

    current_critpath = list_critpath(arg.branch)

    try:
        update_critpath(set(current_critpath), set(new_critpath), arg.branch)
    except KeyboardInterrupt:
        LOG.info("\nInterrupted by user.")
        return_code = 1
    except Exception as err:
        LOG.exception("Caught generic error")
        return_code = 2

    return return_code


if __name__ == '__main__':
    sys.exit(main())
