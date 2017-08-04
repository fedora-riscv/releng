""" get-retired-packages.py - Gets all the packages that have all of the
specified branches marked as inactive
"""
from __future__ import print_function
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
import multiprocessing.pool
from multiprocessing import cpu_count
import argparse
from math import ceil
from functools import partial
import sys
import traceback
import requests

PDC_URL = 'https://pdc.fedoraproject.org'
# These are set to 4 so that there is a performance gain but it should be low
# enough to not overwhelm PDC
MAX_NUM_PROCESSES = 4
NUM_THREADS_PER_PROCESS = 4


def handle_errors(f):
    def _wrapper(*args, **kwargs):
        """ A decorator for `f` that prints tracebacks. """
        try:
            return f(*args, **kwargs)
        except:
            traceback.print_exc()
            raise
    _wrapper.__name__ = f.__name__
    _wrapper.__doc__ = f.__doc__
    return _wrapper


def get_component_branch_page(branch_name, page, page_size=100):
    query_args = {'type': 'rpm', 'name': branch_name, 'active': False,
                  'page_size': page_size, 'page': page}
    pdc_api_query_url = '{0}/rest_api/v1/component-branches/?{1}'.format(
        PDC_URL.rstrip('/'), urlencode(query_args))
    try:
        rv = requests.get(pdc_api_query_url, timeout=30)
    except (requests.ConnectionError, requests.ConnectTimeout):
        print('The connection to PDC failed', file=sys.stderr)
        sys.exit(1)

    try:
        return rv.json()
    except ValueError:
        print('The data returned from PDC was not JSON', file=sys.stderr)
        sys.exit(1)


def get_pkgs_from_page(branch_name, page):
    pkgs_set = set()
    rv_json = get_component_branch_page(branch_name, page)
    # Extract the package names from API results
    for branch_rv in rv_json['results']:
        pkgs_set.add(str(branch_rv['global_component']))

    return pkgs_set


@handle_errors
def get_pkg_branch_status(branch_name):
    # Get total number of branches that fit the query
    component_branch_page_one = \
        get_component_branch_page(branch_name, page=1, page_size=1)
    # Get the total number of pages
    num_pages = int(ceil(component_branch_page_one['count'] / 100.0))
    # Since we are going to multi-thread, we need to make a partial function
    # call so that all the function needs is an iterable to run
    partial_get_pkgs_from_page = partial(get_pkgs_from_page, branch_name)
    # Start processing NUM_THREADS_PER_PROCESS pages at a time
    pool = multiprocessing.pool.ThreadPool(NUM_THREADS_PER_PROCESS)
    pkg_sets = pool.map(partial_get_pkgs_from_page, range(1, num_pages + 1))
    pool.close()
    # Return a set of all the packages from the pages queried
    if pkg_sets:
        return set.union(*pkg_sets)
    else:
        return set()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    help = 'the branches that the returned packages will have retired'
    parser.add_argument('branches', nargs='+', help=help)
    args = parser.parse_args()
    if cpu_count() > MAX_NUM_PROCESSES:
        num_processes = MAX_NUM_PROCESSES
    else:
        num_processes = cpu_count()
    # Process up to num_processes branches at a time in separate processes
    pool = multiprocessing.Pool(processes=num_processes)
    pkg_sets = pool.map(get_pkg_branch_status, args.branches)
    pool.close()

    # Return only the packages that have all the specified branches and are
    # retired
    pkgs = list(set.intersection(*pkg_sets))
    if pkgs:
        for pkg in sorted(pkgs):
            print(pkg)
    else:
        print('No retired packages were returned from the branches: {0}'
              .format(', '.join(args.branches), file=sys.stderr))
