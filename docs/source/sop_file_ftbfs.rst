.. SPDX-License-Identifier:    CC-BY-SA-3.0


==========
File FTBFS
==========

Description
===========

.. note::
    FTBFS = "Fails To Build From Source"

After every mass rebuild, we file FTBFS bugs for the packages that failed to build during mass rebuild.

This should be run after the `mass rebuild builds are merged into main tag`_.

Action
======
The FTBFS bugs are filed in bugzilla.

#. Create a bugzilla bug for FTBFS, use the `previous FTBFS bugzilla bug example`_ if its not created

#. Install `python-bugzilla-cli` on your local machine if its not installed
    ::

        $ sudo dnf install python-bugzilla-cli

#. Update the `massrebuildsinfo.py`
    * epoch
    * buildtag
    * destag
    * tracking_bug

    .. note::
        Most of these values are already updated during mass rebuild, only one that might need updating is `tracking_bug`

#. Update the `mass_rebuild_file_bugs.py`
    * rebuildid

#. Login into bugzilla in the terminal using `bugzilla login` command
    ::

        $ bugzilla login

    .. note::
        Login as `releng@fedoraproject.org`

#. Run `mass_rebuild_file_bugs.py` locally
    ::

        $ python mass_rebuild_file_bugs.py


.. _mass rebuild builds are merged into main tag: https://docs.pagure.org/releng/sop_mass_rebuild_packages.html#post-mass-rebuild-tasks
.. _previous FTBFS bugzilla bug example: https://bugzilla.redhat.com/show_bug.cgi?id=1750908
