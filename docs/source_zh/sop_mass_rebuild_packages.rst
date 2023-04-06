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

Considerations
==============

* The most important thing to keep in mind while doing a mass rebuild is to
  communicate clearly what actions are being performed and the status of the
  rebuild.
* Check in on scripts frequently to avoid a long stalled command from adding
  significant delays in completing the rebuild.
* Check with secondary arches, whether they up-to-date enough with primary,
  create rebuild tag and target when they are. It will then take care of
  rebuilds of the arch specific packages in appropriate kojis.

Actions
=======

Preparatory Steps
-----------------
The following steps may be completed in the weeks leading up to the
scheduled mass rebuild.

#. Create the Mass Rebuild Pagure Issue

    Create an issue on the `Release Engineering issues page`_ that
    points at the schedule for the current release.

    See `the Fedora 27 mass rebuild issue example`_.
   
#. Set up the Mass Rebuild Wiki Page

    The mass rebuild wiki page should answer the following questions for
    maintainers:

    * Why the mass rebuild is happening
    * How to opt out of the mass rebuild

    .. note::
   
        See `the Fedora 26 Wiki example`_.

#. Send out the Mass Rebuild Notice

    Send out the same information posted on the wiki to the
    `devel-announce@lists.fedoraproject.org` mailing list.

    .. note::

         See `the Fedora 26 e-mail example`_.

#. Create a Tag to Contain the Mass Rebuild

    Mass rebuilds require their own tag to contain all related builds. The
    example assumes we are doing a rebuild for Fedora 26.

    ::

        $ koji add-tag f26-rebuild --parent f26

#. Request Package Auto-Signing for New Mass-Rebuild Tag

    File a ticket with `Fedora Infrastructure`_ requesting the new
    mass-rebuild tag be enabled for package auto-signing.

#. Create the Koji Target for the Mass Rebuild

    Using the same `f26-rebuild` tag created in the previous example:

    ::

        $ koji add-target f26-rebuild f26-build

    .. note::

        **koji add-target** *target-name* *buildroot-tag* *destination-tag*
        describes the syntax format above. If the *destination-tag* is not
        specified then it will be the same as the *target-name*.


#. Update Scripts

    The mass rebuild depends on four main scripts from the
    `releng git repository`_. Each one requires some changes in variables
    for each new mass rebuild cycle.

    * mass-rebuild.py
        * buildtag
        * targets
        * epoch
        * comment
        * target
    * find-failures.py
        * buildtag
        * desttag
        * epoch
    * mass-tag.py
    * need-rebuild.py
        * buildtag
        * target
        * updates
        * epoch

Change the following items:

* the build tag, holding tag, and target tag should be updated to reflect the
  Fedora release you're building for
* the ``epoch`` should be updated to the point at which all features that
  the mass rebuild is for have landed in the build system (and a newRepo task
  completed with those features)
* the comment which is inserted into spec changelogs


Starting the Mass Rebuild
-------------------------
The ``mass-rebuild.py`` script takes care of:

* Discovering available packages in koji
* Trimming out packages which have already been rebuilt
* Checking out packages from git
* Bumping the spec file
* Committing the change
* git tagging the change
* Submitting the build request to Koji


#. Connect to the mass-rebuild Machine

    ::

        $ ssh branched-composer.phx2.fedoraproject.org


#. Start a terminal multiplexer

    ::

        $ tmux

#. Clone or checkout the latest copy of the `releng git repository`_.

#. Run the mass-rebuild.py script from *releng/scripts*

    ::

        $ cd path/to/releng_repo/scripts
        $ ./mass-rebuild.py 2>&1 | tee ~/massbuild.out

Monitoring Mass Rebuilds
------------------------
The community has a very high interest in the status of rebuilds and many
maintainers will want to know if their build failed right away. The
``find-failures.py`` and ``need-rebuild.py`` scripts are designed to update
publicly available URLs for stakeholders to monitor.

#. Connect to a Compose Machine

    ::

        $ ssh compose-x86-02.phx2.fedoraproject.org

#. Start a terminal multiplexer

    ::

        $ tmux

#. Clone or checkout the latest copy of the `releng git repository`_

#. Set Up the Rebuild Failures Notification Web Site
    The ``find_failures.py`` script discovers attempted builds that have
    failed. It lists those failed builds and sorts them by package owner.

    ::

        $ while true; do ./find_failures.py > f26-failures.html && cp f26-failures.html /mnt/koji/mass-rebuild/f26-failures.html; sleep 600; done

#. Start a second pane in the terminal emulator

#. Set up the Site for Packages that Need Rebuilt
    The ``need-rebuild.py`` script discovers packages that have not yet been
    rebuilt and generates an html file listing them sorted by package owner.
    This gives external stakeholders a rough idea of how much work is
    remaining in the mass rebuild.

    ::

        $ while true; do ./need-rebuild.py > f26-need-rebuild.html && cp f26-need-rebuild.html /mnt/koji/mass-rebuild/f26-need-rebuild.html; sleep 600; done

Post Mass Rebuild Tasks
-----------------------
Once the mass rebuild script completes, and all the pending builds have
finished, the builds will need to be tagged.  The ``mass-tag.py`` script will
accomplish this task.  The script will:

* Discover completed builds
* Trim out builds that are older than the latest build for a given package
* Tag remaining builds into their final destination (without generating email)

#. Clone or checkout the latest copy of the `releng git repository`_

#. Run the ``mass-tag.py`` script (requires koji kerberos authentication)

    ::

        $ cd path/to/releng_repo/scripts
        $ ./mass-tag.py --source f36-rebuild --target f36

#. Send the final notification to the
   *devel-announce@lists.fedoraproject.org* list

    The contents should look something like this `example email`_.

.. _the Fedora 26 Wiki example: https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild
.. _the Fedora 26 e-mail example: https://lists.fedoraproject.org/archives/list/devel-announce@lists.fedoraproject.org/message/QAMEEWUG7ND5E7LQYXQSQLRUDQPSBINA/
.. _releng git repository: https://pagure.io/releng
.. _Release Engineering issues page: https://pagure.io/releng/issues
.. _example email: https://lists.fedoraproject.org/archives/list/devel@lists.fedoraproject.org/message/QAMEEWUG7ND5E7LQYXQSQLRUDQPSBINA/
.. _Fedora Infrastructure: https://pagure.io/fedora-infrastructure/issues
.. _the Fedora 27 mass rebuild issue example: https://pagure.io/releng/issue/6898
