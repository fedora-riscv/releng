.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
Unretiring a package branch
===========================

Description
===========

Sometimes, packagers request that we *unretire* a package branch that has
previously been retired.

This typically happens on the `master` branch, but could conceivably happen on
any stable or "arbitrary" branch.

Before proceeding further, the release engineer should check that the package
was not previously retired for some Very Good Reason, legal or otherwise.
Decide whether or not to proceed with unretirement accordingly.

Action
======

Unretiring a package consists of the following actions:

- Git revert the `dead.package` file commit in dist-git on the particular branch.
- Unblock the package in koji::

    koji unblock-pkg epel7 TurboGears2

- Set the PDC EOLs for the branch to appropriate future values::

    export PYTHONPATH=scripts/pdc/
    python scripts/pdc/adjust-eol.py fedora TOKEN TurboGears2 rpm epel7 default

- Refresh the pagure acl config to allow pushes.  ssh to `pkgs02` and run::

    PAGURE_CONFIG=/etc/pagure/pagure.cfg pagure-admin refresh-gitolite --project rpms/TurboGears2
