""" Common PDC utility functions, shared by scripts. """

import sys

def prompt(message, force):
    return force or raw_input(message + " [y/N]: ").lower() in ('y', 'yes')


def die(message):
    print("! " + message)
    sys.exit(3)


def ensure_global_component(pdc, package, force):
    """ Ensure that the given global component exists. """
    pdc['global-components']._(name=package)
    results = list(pdc.get_paged(pdc['global-components'], name=package))
    if results:
        print "Found global-components/%s" % package
        return
    message = "global-component %s does not exist.  Create it?" % package
    if not prompt(message, force):
        print "Not creating global-component", package
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


def ensure_component_branches(pdc, package, slas, eol, branch, type, force):
    endpoint = pdc['component-branch-slas']
    # A base query
    base = dict(branch=branch, global_component=package, branch_type=type)
    for sla in slas:
        # See if the sla already exists on the branch:
        results = list(pdc.get_paged(endpoint, sla=sla, **base))
        if results:
            print("  sla {sla: <16} already exists for {branch_type}/"
                  "{global_component}#{branch}".format(sla=sla, **base))
            continue
        message = "Apply sla %r to %r" % (sla, base)
        if not prompt(message, force):
            print("Not applying sla %r to %r" % (sla, base))
            continue
        print("Applying sla %r to %r" % (sla, base))
        payload = dict(
            sla=sla,
            eol=eol,
            branch=dict(
                name=branch,
                global_component=package,
                type=type,
            )
        )
        endpoint._(payload)
