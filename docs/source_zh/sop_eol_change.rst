.. SPDX-License-Identifier:    CC-BY-SA-3.0

================================
Adjust EOLs and SLs on branches
================================

.. note:: This SOP is about adjust EOLs and SLs on so-called "arbitrary"
   branches.  Unretiring a package *also* involves changing the EOL on a
   branch, but you won't find information on that here.  See the unretirement
   SOP for more info there.

Description
===========

With "arbitrary branching", modules can include streams for an RPM that are not
directly associated with a Fedora release.  Modules *themselves* can have
branches not directly associated with a Fedora release.  For instance, our
`python3` module has a `3.6` branch.  The SLs on that module branch all go EOL
on 2018-06-01. **@torsava**, one of the `python3 module maintainers
<https://src.fedoraproject.org/modules/python3k>`_, may request that this
branch have its EOL extended until 2018-12-01.

When a maintainer wants to change EOL on a rpm, module, or container branch,
they need to file a `releng ticket <https://pagure.io/releng/issues>`_
requesting it.  They have no way to do it on their own.  Releng must review the
request, and then process it.

Policy
======

Here are some *policy* guidelines to help you (releng) make decisions about these tickets

- Clarify.  Does the maintainer want the EOL lengthed for an rpm?  Or for a
  module?  Or for a container?  If they just say "increase the EOL for `httpd`,
  please", it is not clear which thing they're really talking about.

- Expect that maintainers generally know *when* their EOL should go until.  You
  don't need to go and research upstream mailing lists to figure out what makes
  sense.  Politely asking the maintainer for some background information on
  *why* the EOL should be changed is good to record in the ticket for
  posterity.  Bonus points if they can provide references to upstream
  discussions that make the request make sense.

- EOLs should *almost always* only be extended into the future.  Shortening an
  EOL should only be done with care.  There might be modules out there that
  depend on an rpm branch with a conflicting EOL of their own.  If a *shorter*
  EOL is requested for an rpm branch, you should verify that no modules that
  depend on it have a conflicting EOL.  If a *shorter* EOL is requested for a
  module branch, you should verify that no other modules require it that have a
  conflicting EOL.

- EOLs should not be arbitrary dates.  At Flock 2017, we `decided on using two
  standard dates <https://pagure.io/fedrepo_req/issue/100>`_ for EOLs to help
  make things less crazy.  You should use December 1st or June 1st of any given
  year for all EOL dates.

- Many branches will *often* have multiple SLs all with the *same* EOL.  I.e.,
  the branch is fully supported until such time as it is totally retired.
  There is no gray area.  However, it is *possible* to have branches with
  piecemeal SLs and EOLs.  A branch may support `bug_fixes` until time X but
  will further support `security_fixes` until time Y.  This is nicely flexible
  for the maintainers, but also introduces complexity.  If a maintainer
  requests piecemeal SL EOLs, ask to make sure they really want this kind of
  complexity.

Action
======

We have a script in the releng repo::

    $ PYTHONPATH=scripts/pdc python3 scripts/pdc/adjust-eol.py -h

.. note:: Run it with `python3`.  It imports `fedrepo_req` which is python3 by default.
   Installing `python2` dependencies should be possible when needed.

Here is an example of using it to increase the SL of the `3.6` branch of the
`python3` module (not the rpm branch)::

    $ PYTHONPATH=scripts/pdc python3 scripts/pdc/adjust-eol.py \
        fedora \
        SOME_TOKEN \
        python3 \
        module \
        3.6 \
        2018-12-01
    Connecting to PDC args.server 'fedora' with token 'a9a1e4cbca122c21580d1fe4646e603a770c5280'
    Found 2 existing SLs in PDC.
    Adjust eol of (module)python3#3.6 security_fixes:2018-06-01 to 2018-12-01? [y/N]: y
    Adjust eol of (module)python3#3.6 bug_fixes:2018-06-01 to 2018-12-01? [y/N]: y
    Set eol to 2018-12-01 on ['(module)python3#3.6 security_fixes:2018-06-01', '(module)python3#3.6 bug_fixes:2018-06-01']
