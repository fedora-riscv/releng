""" Common PDC utility functions, shared by scripts. """
from __future__ import print_function

import copy
import sys

STANDARD_BRANCH_SLAS = {
    'rawhide': {
        'rawhide': '2222-01-01'
    },
    'stable': {
        'rawhide': '2222-01-01'
    },
    'main': {
        'rawhide': '2222-01-01'
    },
    'f38': {
        'bug_fixes': '2024-11-14',
        'security_fixes': '2024-11-14'
    }
}


def prompt(message, force):
    try:
        question = input  # python3
    except NameError:
        question = raw_input  # python2
    return force or question(message + " [y/N]: ").lower() in ('y', 'yes')


def die(message):
    print("! " + message)
    sys.exit(3)


def ensure_global_component(pdc, package, force):
    """ Ensure that the given global component exists. """
    pdc['global-components']._(name=package)
    results = list(pdc.get_paged(pdc['global-components'], name=package))
    if results:
        print("Found global-components/%s" % package)
        return
    message = "global-component %s does not exist.  Create it?" % package
    if not prompt(message, force):
        print("Not creating global-component", package)
        sys.exit(1)
    payload = dict(name=package)
    pdc['global-components']._(payload)


def verify_slas(pdc, slas):
    """ Verify that the given SLAs exist in PDC. """
    for sla in slas:
        endpoint = pdc['component-sla-types']._
        results = list(pdc.get_paged(endpoint, name=sla))
        if not results:
            die("%r is not a valid SLA in PDC.  See %s" % (sla, endpoint))


def ensure_component_branches(pdc, package, slas, eol, branch, type, critpath, force):
    endpoint = pdc['component-branch-slas']
    # A base query
    base = dict(branch=branch, global_component=package, branch_type=type)
    modified = []
    for sla in slas:
        # See if the sla already exists on the branch:
        results = list(pdc.get_paged(endpoint, sla=sla, **base))
        if results:
            continue

        # See if user wants intervention
        message = "Apply sla %r to %r" % (sla, base)
        if not prompt(message, force):
            print("Not applying sla %r to %r" % (sla, base))
            continue

        # Do it.
        modified.append(sla)
        payload = dict(
            sla=sla,
            eol=eol,
            branch=dict(
                name=branch,
                global_component=package,
                type=type,
                critical_path=critpath,
            )
        )
        endpoint._(payload)

    # Report at the end.
    if modified:
        print("Applied %r to %r (critpath %r)" % (modified, base, critpath))
    else:
        print("Did not apply any slas to %r (critpath %r)" % (base, critpath))



def patch_eol(pdc, package, eol, branch, type, force):
    specified_eol = eol
    endpoint = pdc['component-branch-slas']
    # A base query
    query = dict(branch=branch, global_component=package, branch_type=type)
    slas = list(pdc.get_paged(endpoint, **query))
    print("Found %i existing SLs in PDC." % len(slas))

    fmt = lambda s: "({type}){global_component}#{name} {sla}:{eol}".format(**s)
    modified = []
    for sla in slas:
        flattened = copy.copy(sla)
        flattened.update(sla['branch'])

        if specified_eol == 'default':
            if branch not in STANDARD_BRANCH_SLAS:
                raise KeyError("%r is not a standard branch, so we don't know "
                               "a `default` SLA." % branch)
            if sla['sla'] not in STANDARD_BRANCH_SLAS[branch]:
                raise KeyError("%r does not have a default eol for %r" % (
                    sla['sla'], branch))
            eol = STANDARD_BRANCH_SLAS[branch][sla['sla']]

        # See if user wants intervention
        message = "Adjust eol of %s to %s?" % (fmt(flattened), eol)
        if not prompt(message, force):
            print("Not adjusting eol.")
            continue

        # Do it.
        modified.append(fmt(flattened))
        endpoint['%i/' % sla['id']] += dict(eol=eol)

    # Report at the end.
    if modified:
        print("Set eol to %s on %r" % (eol, modified))
    else:
        print("Did not adjust any EOLs.")
