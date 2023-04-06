.. SPDX-License-Identifier:    CC-BY-SA-3.0


======================
Adding New Branch SLAs
======================

Description
===========

In the ArbitraryBranching model, packagers can choose whatever SLAs they want
for the branches of their packages, but they must choose from a subset of
pre-defined SLAs stored in PDC, maintained by releng.

This SOP describes the steps necessary for a release engineer to create a new SLA.

Action
======

Adding a new SLA is simple.  It involves running a script in the releng repo, with an authorized token.
There is a token available on `pdc-backend01` in the `/etc/pdc.d/` directory.


::

    $ ./scripts/pdc/insert-sla.py
    Name of the SLA:  wild_and_cavalier
    Description of the SLA:  Anything goes!  This branch may rebase at any time.  No stability guarantees provided.

Verification
============

Verifying that the SLA is present is simple:  visit the `appropriate PDC
endpoint <https://pdc.fedoraproject.org/rest_api/v1/component-branch-slas/>`_
and verify that your newly-added SLA is present.
