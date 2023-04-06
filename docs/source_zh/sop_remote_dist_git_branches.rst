.. SPDX-License-Identifier:    CC-BY-SA-3.0


========================
Remove dist-git branches
========================

Description
===========
Release Engineering is often asked by maintainers to remove branches in dist-git
by maintainers.

Action
======
#. Log into batcave01

   ::

        ssh <fas-username>@batcave01.iad2.fedoraproject.org

#. Get root shell 

#. Log into pkgs01.iad2.fedoraproject.org
   ::

        ssh pkgs01.iad2.fedoraproject.org

#. Change to the package's directory

   ::

        cd /srv/git/rpms/<package>.git/

#. Remove the branch

   ::

        git branch -D <branchname> </pre>

Verification
============
To verify just list the branches.

::

    git branch

Consider Before Running
=======================
Make sure that the branch in question isn't one of our pre-created branches
``f??/rawhide``, ``olpc?/rawhide``, ``el?/rawhide``
