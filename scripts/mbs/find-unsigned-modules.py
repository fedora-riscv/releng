#!/usr/bin/env python
""" find-unsigned-modules.py - Produce a list of unsigned modules from a given list.

    Usage:  find-unsigned-modules.py NS[V] NS[V] NS[V] ...

Example:

    Usage:  find-unsigned-modules.py shared-userspace-f26 base-runtime-f26-2017070101

Consult pungi-fedora/variants-modular.xml for a list of modules in a compose.

"""

from __future__ import print_function

import sys

import koji
import kobo.rpmlib
import dogpile.cache
import pdc_client
from pungi.phases.pkgset.sources.source_koji import get_module

cachefile = "/var/tmp/find-unsigned-modules-cache.dbm"
cache = dogpile.cache.make_region().configure(
    'dogpile.cache.dbm',
     expiration_time=600,
     arguments={"filename": cachefile},
)


def resolve_modules(modules):
    for module in modules:
        yield _resolve_module(module)


@cache.cache_on_arguments()
def _resolve_module(module):
    pdc = pdc_client.PDCClient(server='fedora', develop=True)
    return get_module(pdc, module)


@cache.cache_on_arguments()
def _get_rpm_info(module):
    session = koji.ClientSession('https://koji.fedoraproject.org/kojihub')
    session.multicall = True
    for rpm in module['rpms']:
        parsed = kobo.rpmlib.parse_nvra(rpm)
        session.getRPM(parsed)
    return session.multiCall()


@cache.cache_on_arguments()
def _get_signatures(rpms):
    session = koji.ClientSession('https://koji.fedoraproject.org/kojihub')
    session.multicall = True
    for info in rpms:
        assert len(info) == 1, len(info)
        info = info[0]
        session.queryRPMSigs(info['id'])
    return session.multiCall()


@cache.cache_on_arguments()
def module_signature_state(module):
    rpms = _get_rpm_info(module)
    signatures = _get_signatures(rpms)

    seen_keys = set()
    for signature in signatures:
        assert len(signature) == 1, len(signature)
        signature = signature[0]
        new_keys = set([r['sigkey'] for r in signature if r['sigkey']])
        # If any rpm is missing signatures, then bail.
        if not new_keys:
            return None
        seen_keys.update(new_keys)
    return seen_keys or None


def retrieve_modules(modules):
    modules = resolve_modules(modules)
    for module in modules:
        module['signed'] = module_signature_state(module)
        yield module


if __name__ == '__main__':
    index = sys.argv.index('find-unsigned-modules.py') + 1
    modules = sys.argv[index:]

    print("Using cache file", cachefile, file=sys.stderr)
    modules = retrieve_modules(modules)

    for module in modules:
        if module['signed']:
            print("+", module['variant_uid'], "with tag", module['koji_tag'],
                "is signed with", ', '.join(module['signed']))
        else:
            print("-", module['variant_uid'], "with tag", module['koji_tag'],\
                "is not signed.")
