.. SPDX-License-Identifier:    CC-BY-SA-3.0


======================
Adding Side Build Tags
======================

Description
===========
Bigger Features can take a while to stabilize and land or need a large number
of packages to be built against each other, this is easiest served by having a
separate build tag for the development work.  This SOP will describe the steps
necessary to prepare the new build target.

Action
======
Engineers should be aware that adding side build targets incurs extra
newRepo tasks in the koji.

Research Tag
------------

#. Verify whether a tag already exists.

   The typical tag format is *PRODUCT*-*DESCRIPTOR*. The *DESCRIPTOR* should
   be something brief that clearly shows why the tag exists.

   .. note::

      Don't think too hard about what makes a good descriptor.  The
      descriptor for the XFCE version 4.8 side-build target was *xfce48*.
      KDE often simply uses *kde* as its descriptor.  Use best judgement and
      if in doubt ask in IRC on ``#fedora-releng``.

   .. admonition:: EPEL6

      ::

         $ koji taginfo epel6-kde

   .. admonition:: EPEL7

      ::

         $ koji taginfo epel7-kde

   .. admonition:: Fedora

      ::

         $ koji taginfo f28-kde

   .. note::
      If the tag already exists, continue searching for an available tag
      by appending ``-2`` and incrementing the number by one until an
      available tag is found.  For example, if ``f28-kde`` already exists
      then search for ``f28-kde-2``, ``f28-kde-3``, and so on until a
      suitable tag is found.

#. Determine the appropriate architectures.

   .. admonition:: EPEL6

      ::

         $ koji taginfo dist-6E-epel-build

   .. admonition:: EPEL7

      ::

         $ koji taginfo epel7-build

   .. admonition:: Fedora

      ::

         $ koji taginfo f28-build

Create Side Build Target
------------------------

#. Create the proper tag.

   Note the slightly different syntax depending on
   which product needs the side-build target and the comma delimited list of
   architectures based on the information from a previous step.


   .. admonition:: EPEL6

      ::

         $ koji add-tag epel6-kde --parent=dist-6E-epel-build --arches=i686,x86_64,ppc64

   .. admonition:: EPEL7

      ::

         $ koji add-tag epel7-kde --parent=epel7-build --arches=aarch64,x86_64,ppc64,ppc64le

   .. admonition:: Fedora

      ::

         $ koji add-tag f28-kde --parent=f28-build --arches=armv7hl,i686,x86_64,aarch64,ppc64,ppc64le,s390x

#. Create the target.

   .. admonition:: EPEL6

      ::

         $ koji add-target epel6-kde epel6-kde

   .. admonition:: EPEL7

      ::

         $ koji add-target epel7-kde epel7-kde

   .. admonition:: Fedora

      ::

         $ koji add-target f28-kde f28-kde

#. Find the taskID for the newRepo task associated with the newly created
   target.

   ::

      $ koji list-tasks --method=newRepo
      ID       Pri  Owner                State    Arch       Name
      25101143 15   kojira               OPEN     noarch     newRepo (f28-kde)


#. Ensure the newRepo task is being run across all architectures.

   ::

      $ koji watch-task 25101143
      Watching tasks (this may be safely interrupted)...
      25101143 newRepo (f28-kde): open (buildvm-14.phx2.fedoraproject.org)
      25101154 createrepo (i386): closed
      25101150 createrepo (ppc64le): closed
      25101152 createrepo (ppc64): closed
      25101151 createrepo (aarch64): closed
      25101149 createrepo (armhfp): closed
      25101153 createrepo (s390x): open (buildvm-ppc64le-04.ppc.fedoraproject.org)
      25101148 createrepo (x86_64): open (buildvm-aarch64-21.arm.fedoraproject.org)
      

#. Request Package Auto-Signing for New Tag

   File a ticket in `pagure infrastructure`_ requesting the new tag be enabled
   for package auto-signing.

#. Update the Pagure Issue

   Update the issue according to the following template which assumes a side
   target was made for KDE under Fedora 28.
      *TAG_NAME* has been created:

      $ koji add-tag f28-kde --parent=f28-build --arches=armv7hl,i686,x86_64,aarch64,ppc64,ppc64le,s390x

      $ koji add-target f28-kde f28-kde

      You can do builds with:
      
      $ fedpkg build --target=f28-kde

      Let us know when you are done and we will move all the builds into
      f28.


Cleanup
=======
Fedora Release Engineering is responsible for merging the packages from the
side-build target and tag back into the main tag. The requestor will update
the original ticket when ready for the procedure outlined below.

#. Remove the target

   ::

      $ koji remove-target <SIDE_TAG_NAME>

#. Merge side build back to main target.

   Get the latest checkout from `Fedora Release Engineering Repository`_
   and run the `mass-tag.py` from the scripts directory.

   ::

      $ ./mass-tag.py --source <SIDE_TAG_NAME> --target <MAIN_TAG_NAME> > mass_tag.txt

   .. note::
      The *MAIN_TAG_NAME* for Fedora is typically the pending subtag, e.g.
      ``f28-pending`` when bodhi is not managing updates. After bodhi is
      enabled and managing updates then merge into ``f28-updates-candidate``.

#. Paste Output to the Original Ticket

   Paste the output from mass-tag.py into the pagure/releng ticket to show
   what packages were merged and what packages need rebuilding for those who
   work on the buildroot.

Tags are **never** removed.

Consider Before Running
=======================

* Is the amount of work to be done worth the cost of newRepo tasks.
* If there is only a small number of packages  overrides may be better.
* Is there a mass-rebuild going on? no side tags are allowed while a mass
  rebuild is underway

.. _pagure infrastructure: https://pagure.io/fedora-infrastructure/issues
.. _Fedora Release Engineering Repository: https://pagure.io/releng/
