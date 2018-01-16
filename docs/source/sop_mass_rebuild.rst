.. SPDX-License-Identifier:    CC-BY-SA-3.0


============
Mass Rebuild
============

Description
===========

Periodically we do mass rebuilds of rawhide during the development cycle. This
SOP will outline the steps necessary to do this.

Assumptions
===========
This assumes that the mass rebuild has already been approved and scheduled via
release engineering and FESCo. Coordinate with infrastructure as well for any
needed koji updates.

This also assumes that the mass rebuild does not need to be done in dependency
order, and that the mass rebuild does not involve a ABI change.

Set up a web page for maintainers & send notice about rebuild
=============================================================

Firstly, describe the mass rebuild for maintainers; why it's being done, and
how they can opt out in a wiki page. See `the Fedora 26 example`_.

== Update releng scripts ==

Release engineering scripts for mass rebuilds live in the `releng git
repository`_. You need to edit the following scripts:

* mass-rebuild.py
* find-failures.py
* mass-tag.py
* need-rebuild.py

Change the following items:

* the build tag, holding tag, and target tag should be updated to reflect the
  Fedora release you're building for
* the ``epoch`` tag should be updated to the point at which all features that
  the mass rebuild is for have landed in the build system (and a newRepo task
  completed with those features)
* the comment which is inserted into spec changelogs

== Create the rebuild holding tag ==

The ``add-tag`` command is used for creating the rebuild holding tag.

::

    $ koji add-tag --help
    Usage: koji add-tag [options] name
    (Specify the --help global option for a list of other help options)

    Options:
      -h, --help       show this help message and exit
      --parent=PARENT  Specify parent
      --arches=ARCHES  Specify arches


The options let you specify a parent for the holding tag.

For example, if we wanted to create a rebuild holding tag for Fedora 26
development we would issue:

::

    koji add-tag f26-rebuild --parent f26

.. note::
Please ask someone from infra to enable autosigning for newly created
``f26-rebuild`` tag.

Create the rebuild target
=========================

The ``add-target`` command is used for creating the rebuild target.

::

    $ koji add-target --help
    Usage: koji add-target name build-tag <dest-tag>
    (Specify the --help global option for a list of other help options)

    Options:
      -h, --help  show this help message and exit

The arguments define the name of the target, the build-tag to use, and what
tag to apply to builds as they complete.  To continue our example, the
following command would add the target for the Fedora 26 mass rebuild:

::

    koji add-target f26-rebuild f26-build

When the dest-tag is not specified, it is assumed that the dest-tag is the
same as the name of the target, in this case ``f26-rebuild``.

Building the packages
=====================

The ``mass-rebuild.py`` script takes care of:

* Discovering available packages in koji
* Trimming out packages which have already been rebuilt
* Checking out packages from git
* Bumping the spec file
* Committing the change
* git tagging the change
* Submitting the build request to Koji

The requirements for the script are as follows:

* Ran as a user with a proper koji cert setup
* Ran as a user with commit access to all packages
* Ran as a user with a valid ssh agent for git actions
* Ran on a system with a reliable network connection

.. note::
In Fedora Infra, the user is ``mass-rebuild``

The script has error checking at every step of the way and will gracefully
recover and continue on with the next package.  It does the rebuilds in an
alphanumerical order (provided by python sorted()) by source package name, and
it does a complete checkout, bump, commit, tag, and build one package at a
time. The current bottleneck when mass rebuilding is the git server, but
generally 4 packages per minute can be processed.

The script isn't very resource intensive, once it has discovered the available
packages and trimmed out the things which have already been rebuilt.  Those
tasks require a fair amount of cpu time to process the XML data returned by
koji. Once the script has moved on to the git, bump, tag, build phase the
resource usage is light, mostly network to do the git checkouts.

Tips
----

The script logs everything to stderr and stdout, so it is generally a good idea
to redirect and capture the output to a log file, with something like
``2>&1 | tee massbuild.out``.

Running mass-rebuild.py
-----------------------

* ssh into branched-composer.phx2.fedoraproject.org
* Change to mass-rebuild user
* Clone `releng repo`_
* cd to releng/scripts/
* ./mass-rebuild.py 2>&1 | tee massbuild.out

Track the failures
------------------

Failures can happen at any stage.  Missing git module, no spec file to bump,
malformed spec file causing the bump script to exit, git commit failures,
tagging failures, and even koji outages.  Finally the build itself may fail.

The most common failures are build failures, and there is a script to deal
with those (``find-failures.py``)  More on that later.

Outside of build failures, the rest of the failures happen leading up to the
submission of the build, and can be tracked via the mass-rebuild script output.
Any error that the script detects will be output to stderr and will contain the
"failed" keyword.  Searching the output can find these failures, which will
look like:

::

    GMT failed tag: Command '['make', 'tag']' returned non-zero exit status -9

    PyOpenGL failed checkout: Command '['git', '-d', ':ext:jkeating@git.fedoraproject.org:/git/pkgs', 'co', 'PyOpenGL']' returned non-zero exit status -9

    R-BSgenome.Celegans.UCSC.ce2 failed spec check

    eggdbus failed commit: Command '['git', 'commit', '-m', '- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild']' returned non-zero exit status 1

    gupnp-ui failed bumpspec: Command '['rpmdev-bumpspec', '-u', 'Fedora Release Engineering <rel-eng@lists.fedoraproject.org>', '-c', '- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild', '/home/jkeating/massbuild/gupnp-ui/devel/gupnp-ui.spec']' returned non-zero exit status 1


Because stderr flushes immediately it may be hard to find the stdout that
matches the error.  However just repeating the command can often enough show
you what is going on.  Here is a list of common issues and the typical solution:

* checkout failure: Module may not have been added to git yet, skip it.
* spec check: Module may have been retired but not blocked from koji.  Verify
  and block it.
* bumpspec failed: Bump, commit, tag, build manually.  Optionally fix the spec
  so that bumspec works in the future.
* commit failed: Module may have been changed or git / ssh outage.  Repeat
  manually
* git tag failed: Most often this is due to NVR collisions with other branches
  or previous builds.  Re-bump and commit/tag/build manually.
* build submission failed: usually due to a koji or local network outage.
  Re-submit the build manually.

In all cases of fixing failures, verify that no newer build has been done in
the mean time.

find-failures.py
----------------

This script will discover attempted builds that have failed, and then generate
an html file that lists the failed builds (as a link to the build failure) and
sorts them by package owner.  It requires koji installed on the host it runs on.

As the build logs expire, this script is only useful for the first few weeks
after the mass rebuild attempt.

This script should be setup to run often and the output put somewhere public.
This can be tricky if you are running it and uploading the output via ssh as
you will need either an active ssh agent or an open shared socket.  The script
is somewhat resource intensive as it processes a lot of XML from koji.
Updating once an hour is reasonable.

Running find-failures.py
------------------------

* ssh into compose-x86-01.phx2.fedoraproject.org
* Clone `releng git repository`_
* cd to releng/scripts/
* while true; do ./need-rebuild.py > f26-need-rebuild.html && cp f26-need-rebuild.html /mnt/koji/mass-rebuild/f26-need-rebuild.html; sleep 600; done

.. note::
Make sure you run this in screen or tmux

need-rebuild.py
---------------

This script will discover packages that have a need to be rebuilt and haven't
been yet.  It will then generate an html file that lists the packages (as a
link to the package page in koji) and sorts them by package owner.  It requires
koji installed on the host it runs on.

This script should be setup to run often and the output put somewhere public.
This can be tricky if you are running it and uploading the output via ssh as
you will need either an active ssh agent or an open shared socket.  The script
is somewhat resource intensive as it processes a lot of XML from koji.
Updating once an hour is reasonable.

Running need-rebuild.py
------------------------

* ssh into compose-x86-01.phx2.fedoraproject.org
* Clone `releng git repository`_
* cd to releng/scripts/
* while true; do ./find_failures.py > f26-failures.html && cp f26-failures.html /mnt/koji/mass-rebuild/f26-failures.html; sleep 600; done

.. note::
Run this in another screen or tmux session from find-failues.py

Tag the builds
==============

Once the mass rebuild script completes, and all the pending builds have
finished, the builds will need to be tagged.  The ``mass-tag.py`` script will
accomplish this task.  The script will:

* Discover completed builds
* Trim out builds that are older than the latest build for a given package
* Tag remaining builds into their final destination (without generating email)

The script is fairly fast.  The longest time is taken processing the XML from
koji to discover the builds and weed out builds that are not the latest.  The
final tag action is very quick.  Output will go to stdout and should be saved
for later review.

Running mass-tag.py
-------------------

* Clone `releng git repository`_
* cd to releng/scripts/
* ./mass-tag.py --source f26-rebuild --target f26-pending

Consider Before Running
=======================

* The most important thing to keep in mind while doing a mass rebuild is to
  communicate clearly what actions are being performed and the status of the
  rebuild.
* Check in on scripts frequently to avoid a long stalled command from adding
  significant delays in completing the rebuild.
* Check with secondary arches, whether they up-to-date enough with primary,
  create rebuild tag and target when they are. It will then take care of
  rebuilds of the arch specific packages in appropriate kojis.

Email
-----

Once the mass rebuild is done, send an email to ``devel-announce@lists.fedoraproject.org``

`Email Example`_


.. _the Fedora 26 example: https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild
.. _releng git repository: https://pagure.io/releng
.. _Email Example: https://lists.fedoraproject.org/archives/list/devel@lists.fedoraproject.org/message/QAMEEWUG7ND5E7LQYXQSQLRUDQPSBINA/
