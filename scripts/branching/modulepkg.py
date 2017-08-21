#!/usr/bin/python3
#
# modulepkg.py - A utility to track modules which contain a specific package
#                optionally limited to its branch.
#
# Copyright (C) 2017 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0+
#
# Authors:
#     Filip Valder <fvalder@redhat.com>


import argparse
import concurrent.futures
import inspect
import logging
import modulemd
import requests
import requests_cache
import sys
import time

from pdc_client import PDCClient
from yaml import dump


requests_cache.install_cache('modulepkg_cache')
log = logging.getLogger(__name__)


MODULES_SRC_URL = "https://src.fedoraproject.org/modules/"
PDC_DEVELOP = True
PDC_URL_PROD = "https://pdc.fedoraproject.org/rest_api/v1/"
PDC_URL_STG = "https://pdc.stg.fedoraproject.org/rest_api/v1/"
PDC_SSL_VERIFY = True
THREADS = 4


class PDC(object):
    def __init__(self, staging):
        self.query_args = {}
        self.latest_only = True

        if staging:
            server = PDC_URL_STG
        else:
            server = PDC_URL_PROD
        log.debug("PDC URL: %s", server)

        if 'ssl_verify' in inspect.getargspec(PDCClient.__init__).args:
            # New API
            self.session = PDCClient(
                server=server,
                develop=PDC_DEVELOP,
                ssl_verify=PDC_SSL_VERIFY,
            )
        else:
            # Old API
            self.session = PDCClient(
                server=server,
                develop=PDC_DEVELOP,
                insecure=not PDC_SSL_VERIFY,
            )
        log.debug("PDC session: %s", self.session)

    def get_modules(self, **kwargs):
        """
        Query PDC with query parameters in kwargs and return a list of modules
        which contain (latest) modules of each (module_name, module_version).

        :param kwargs: query parameters in keyword arguments, should only
                       provide valid query parameters supported by PDC's module
                       query API.
        :return: a list of modules
        """
        self.query_args.update(kwargs)
        log.debug("PDC query params: %s", self.query_args)
        mods = self.session['unreleasedvariants'](page_size=-1,
                                                  **self.query_args)
        modules = []
        latest_modules = []
        for (name, version) in set([(m.get('variant_name'),
                                     m.get('variant_version'))
                                    for m in mods]):
            found_mods = []
            for m in mods:
                if (name == m.get('variant_name') and
                   version == m.get('variant_version')):
                    found_mods.append(m)

            modules.extend(found_mods)
            latest_modules.append(sorted(
                found_mods, key=lambda x: x['variant_release']).pop())

        if self.latest_only:
            return latest_modules

        return modules


def setup_logging(debug=False, verbose=False):
    # Set log level and format
    if debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s: %(threadName)s: %(levelname)s: %(message)s',
    )

    # Log in UTC
    formatter.converter = time.gmtime

    # Log to console
    console_logger = logging.StreamHandler()
    if debug:
        console_logger.setLevel(logging.DEBUG)
    elif verbose:
        console_logger.setLevel(logging.INFO)
    else:
        console_logger.setLevel(logging.WARNING)
    console_logger.setFormatter(formatter)
    log.addHandler(console_logger)


def process_module(module, package, parser_args):
    """
    Process module for a package given by name

    :param module: a module dict as returned by PDC
    :param package: a package name (str)
    :param parser_args: parser args
    :return: a dict containing information about modules
             (or None if filtered by CLI args)
    """
    m = module
    m_dict = dict()
    filtered = False

    log.debug("Processing module: %s", m['variant_uid'])

    m_dict['module_nsv'] = '{}:{}:{}'.format(
        m['variant_id'], m['variant_version'], m['variant_release'])
    if any([parser_args.filter_branch,
            parser_args.filter_api,
            parser_args.filter_profile]):
        # Load information about module from PDC
        mmd_pdc = modulemd.ModuleMetadata()
        mmd_pdc.loads(m['modulemd'])
        log.debug("Module metadata excerpt from PDC: <ModuleMetadata:"
                  " mdversion: {0.mdversion}, name: '{0.name}', stream: "
                  "'{0.stream}', version: {0.version}, summary: '{0.summary}'>"
                  .format(mmd_pdc))
        module_ref = mmd_pdc.xmd['mbs']['commit']
        # Load information about module from dist-git
        url = "{0}/{1}/raw/{2}/f/{1}.yaml".format(
            MODULES_SRC_URL, m['variant_name'], module_ref)
        log.debug("Requesting module metadata from URL: %s", url)
        r = requests.get(url)
        mmd = modulemd.ModuleMetadata()
        mmd.loads(r.text)
        log.debug("Module metadata excerpt from dist-git: <ModuleMetadata:"
                  " mdversion: {0.mdversion}, name: '{0.name}', stream: "
                  "'{0.stream}', version: {0.version}, summary: '{0.summary}'>"
                  .format(mmd))
        mmd_rpm = mmd.components.rpms.get(package)

        # Process filters
        if parser_args.filter_branch:
            m_dict['ref'] = mmd_rpm.ref
        if parser_args.filter_api:
            api = package if parser_args.filter_api == 1 \
                          else parser_args.filter_api
            if api not in mmd.api.rpms:
                filtered = True
        if parser_args.filter_profile:
            profile = 'default' if parser_args.filter_profile == 1 \
                                else parser_args.filter_profile
            try:
                mmd_profile = mmd.profiles[profile]
            except KeyError:
                log.error('Module profile \'%s\' not found', profile)
                log.info("Filtered module: %s", m['variant_uid'])
                return None
            if package not in mmd_profile.rpms:
                filtered = True

    # return module or None (if filtered)
    if not filtered:
        return m_dict
    log.info("Filtered module: %s", m['variant_uid'])
    return None


def process_packages(parser_args):
    """
    Generate list of packages and their modules

    :param args: parser args containing 'packages' (list)
    :return: a list of dicts
    """
    pkgs = []
    for name in args.packages:
        log.info("Getting information for package: %s", name)
        modules = pdc.get_modules(component_name=name)
        log.info("Number of modules found: %s", len(modules))
        m_info = dict()
        m_info[name] = []
        # Walk through modules
        with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as e:
            f2m = {e.submit(
                process_module, m, name, parser_args): m for m in modules}
            for future in concurrent.futures.as_completed(f2m):
                result = future.result()
                if result:
                    m_info[name].append(result)
            m_info[name] = sorted(m_info[name], key=lambda x: x['module_nsv'])
        pkgs.append(m_info)
    return pkgs


def enhance_descriptions(pkgs):
    """
    Enhance descriptions of the package list

    :param pkgs: a list of dicts (output of process_packages)
    :return: a list of dicts
    """
    for pkg in pkgs:
        for k, v in pkg.items():
            for m in v:
                m['Module (name:stream:version)'] = m.pop('module_nsv')
                if 'ref' in m:
                    m['Reference'] = m.pop('ref')
    return pkgs


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Look up modules for packages, filter them by various"
                    " criteria and print YAML output")
    parser.add_argument("-d", "--debug", default=False, action="store_true",
                        help="Show debug information")
    parser.add_argument("-v", "--verbose", default=False, action="store_true",
                        help="Be more verbose")
    parser.add_argument("-c", "--compact", default=False,
                        action="store_true", help="A more compact output")
    parser.add_argument("-s", "--short-descriptions", default=False,
                        action="store_true", help="Use short (greppable)"
                        " descriptions")
    parser.add_argument("packages", nargs="*", metavar="package",
                        help="Package(s) to look up for depending modules")
    parser.add_argument(
        "--filter-branch", default="ALL", metavar="BRANCH",
        help="Limit the package(s) to a specific branch as defined in dist-git"
             " within list of components. Default: %(default)s")
    parser.add_argument(
        "--filter-api", default=None, nargs='?', const=1,
        metavar="API",
        help="If supplied, filter modules by API. Default: <package>")
    parser.add_argument(
        "--filter-profile", default=None, nargs='?', const=1,
        metavar="PROFILE",
        help="If supplied, filter modules by profile containing this package."
             " Default: 'default'")
    parser.add_argument(
        "--all-releases", default=False, action="store_true",
        help="By default, only latest module releases are listed. This flag"
             " causes all module releases to be listed")
    parser.add_argument(
        "--include-inactive", default=False, action="store_true",
        help="By default, only active modules are taken in mind. This flag"
             " causes both active/inactive modules to be looked up")
    parser.add_argument(
        "--staging", default=False, action="store_true",
        help="Talk to staging PDC service, instead of production")
    args = parser.parse_args()
    _parser_args = args

    # Set logging
    setup_logging(args.debug, args.verbose)

    if not args.packages:
        log.critical("No package name(s) provided")
        sys.exit(2)
    kwargs = dict()

    # Prepare query args for PDC etc.
    if args.filter_branch == "ALL":
        log.info("Gathering information about all branches"
                 " (may take a long time)")
        args.filter_branch = True
    else:
        log.info("Requested branch: %s", args.filter_branch)
        kwargs['component_branch'] = args.filter_branch
        args.filter_branch = False
    if not args.include_inactive:
        kwargs['active'] = 'true'

    # PDC client session
    pdc = PDC(args.staging)
    pdc.query_args = kwargs
    pdc.latest_only = True if not args.all_releases else False

    # Process packages and generate list containing all information
    if not args.short_descriptions:
        pkgs = enhance_descriptions(process_packages(args))
    else:
        pkgs = process_packages(args)

    # Print the list as YAML
    yaml_kwargs = {'default_flow_style': False} if not args.compact else {}
    print(dump(pkgs, allow_unicode=True, **yaml_kwargs))
