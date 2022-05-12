.. SPDX-License-Identifier:    CC-BY-SA-3.0


=======================
Mass Rebuild of Modules
=======================

Description
===========

Periodically we do mass rebuilds of modules in rawhide during the development cycle. This
SOP will outline the steps necessary to do this.

Assumptions
===========
This assumes that the mass rebuild has already been approved and scheduled via
release engineering and FESCo. Coordinate with infrastructure as well for any
needed updates.

Considerations
==============

* The most important thing to keep in mind while doing a mass rebuild is to communicate clearly what actions are being performed and the status of the rebuild.
* Check in on scripts frequently to avoid a long stalled command from adding significant delays in completing the rebuild.

Actions
=======

Preparatory Steps
-----------------
The following steps should be completed after the `mass rebuild of packages`_ is done.

#. Update Scripts

The mass rebuild depends on two main scripts from the `releng git repository`_. Each one requires some changes in variables for each new mass rebuild cycle.

    * *mass-rebuild-modules.py*
        * rebuildid
    * *massrebuildsinfo.py*
        * module_mass_rebuild_epoch
        * module_mass_rebuild_platform

Change the following items:

* the ``rebuildid`` to match the release for which you are mass rebuilding modules as per in massrebuildsinfo.py
* ``module_mass_rebuild_epoch`` mostly will be the epoch of mass rebuild of packages
* ``module_mass_rebuild_platform`` should be the rawhide module platform


Starting the Mass Rebuild of Modules
------------------------------------
The ``mass-rebuild-modules.py`` script takes care of:

* Discovering available available modules from PDC
* Find the module info from mbs and check if a module build is submitted after the epoch date
* Checking out modules from dist-git
* Switching to appropriate stream
* Find modulemd file
* Use libmodulemd to determine if this module stream applies to this platform version
* If needs rebuilding, committing the change
* Push the commit
* Submitting the build request through mbs


#. Connect to the mass-rebuild Machine

    ::

        $ ssh compose-branched01.iad2.fedoraproject.org


#. Start a terminal multiplexer

    ::

        $ tmux

#. Clone or checkout the latest copy of the `releng git repository`_.

#. Run the `mass-rebuild-modules.py` script from *releng/scripts*

    ::

        $ cd path/to/releng_repo/scripts
        $ ./mass-rebuild-modules.py <path_to_token_file> build --wait 2>&1 | tee ~/massbuildmodules.out

.. note::

        The token file should be located in infra's private ansible repo, or ask infra to get it to you using this `process`_.

.. note::

        The `build` option is really important to pay attention, since the mass branching of modules will also use the same script, just changing the option to `branch` and `module_mass_branching_platform` in `massrebuildsinfo.py`

Post Mass Rebuild Tasks
-----------------------
Once the module mass rebuild is done, send an email to the devel-announce@ list

#. Send the final notification to the
   *devel-announce@lists.fedoraproject.org* list

.. _releng git repository: https://pagure.io/releng
.. _process: https://pagure.io/fedora-infrastructure/issue/8048#comment-587789
.. _mass rebuild of packages: https://docs.pagure.org/releng/sop_mass_rebuild_packages.html
