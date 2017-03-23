.. SPDX-License-Identifier:    CC-BY-SA-3.0


================
Composing Fedora
================

Description
===========
All composes are defined by configuration files kept in the `pungi-fedora repository`_.

Composes fall into two categories. They may be release candidates created on demand
or nightly composes set to run at a scheduled time each day.

=============== ===================== =======================
Compose Name    Configuration File    Compose Script
=============== ===================== =======================
Atomic          fedora-atomic.conf    twoweek-nightly.sh
Docker          fedora-docker.conf    docker-nightly.sh
Cloud           fedora-cloud.conf     cloud-nightly.sh
Modular         fedora-modular.conf   modular-nightly.sh
Nightly         fedora.conf           nightly.sh
=============== ===================== =======================

When Quality Engineering (QE) requests a Release Candidate (RC) they do so by opening
an issue in the releng repository on pagure. Release candidate composes are not
currently automated.

=============== ===================== =======================
Compose Name    Configuration File    Compose Script
=============== ===================== =======================
Alpha           fedora-alpha.conf     release-candidate.sh
Beta            fedora-beta.conf      release-candidate.sh
GA              fedora-final.conf     release-candidate.sh
=============== ===================== =======================

.. note::
   Fedora 26 was the last release to include an Alpha release candidate.


Action
======
The following procedures are for release candidates only. They do not apply to the
scheduled nightly composes.

Review Compose Tags
-------------------
#. List any pre-existing builds in the current compose tag

   ::

        $ koji list-tagged f[release_version]-compose

#. Verify pre-existing builds are in compose tags

   The tagged builds from the previous composes should all be present in the
   output from the previous step. Consult the request ticket for the list
   of builds expected in this output.

   .. note::
      The very first run of an Alpha, Beta, or GA compose should have no builds
      listed under the compose tag. It is important to clear pre-existing builds
      from the compose tag when moving between the Alpha, Beta and RC composes.
      Verify that these builds were removed.

      ::

           $ koji list-tagged f[release_version]-compose
           $ koji untag-build --all f[release_version]-compose [build1 build2 ...]

   .. note::
      The order in which packages are added into the f[release_version]-compose tag
      matter. If the builds are untagged erroneously then special attention should
      be given to adding them back correctly.


#. Add builds specified by QE to the current compose tag

   ::

        $ koji tag-build f[release_version]-compose [build1 build2 ...]

   .. note::
       These steps may be completed on a local machine as long as the user has
       appropriate permissions in the koji tool.

Package Signing before the Compose
----------------------------------
#. Check for unsigned packages

   ::

        $ koji list-tagged f[release_version]-signing-pending

   .. note::
      If there are unsigned builds then wait for the automated queue to pick
      them up and sign them. Contact a member of the Fedora infrastructure team
      if the package signing has taken more than thirty minutes.


Running the Compose
-------------------
#. Update the pungi-fedora config file
   Composes use a configuration file to construct the compose. Each
   compose uses its own configuration. The ``global_release`` variable
   should start from 1.1 and the second number should increment each time
   a new compose is created.

   * Alpha - ``fedora-alpha.conf``
   * Beta - ``fedora-beta.conf``
   * RC - ``fedora-final.conf``

#. Log into the compose backend

   ::

        $ ssh compose-x86-01.phx2.fedoraproject.org

#. Open a screen session

   ::

        $ screen

#. Obtain the pungi-fedora branch for the current compose

   The first time any user account executes a compose the pungi-fedora
   git repository must be cloned. The compose candidate script that
   invokes pungi should be run from 
   ``compose-x86-01.phx2.fedoraproject.org``.

   ::

        $ git clone ssh://git@pagure.io/pungi-fedora.git

   Enter the pungi-fedora directory.

   ::

        $ cd pungi-fedora

   If the clone step above was not required then fully update the existing
   repository checkout from pagure.

   ::

        $ git fetch origin
        $ git checkout f[release_version]
        $ git pull origin f[release_version]

#. Run the compose

   ::

        $ sudo ./release-candidate.sh [Alpha|Beta|RC]-#.#

   The numbering scheme begins with 1.1 and the second number is incremented
   after each compose.

   .. note::
      Pungi requires numbers in the format #.# as an argument. It is because
      of this that composes always start with the number 1 and the second
      number is incremented with each compose.

   .. note::
       If the compose fails with a directory missing error, then create
       the compose directory with ``mkdir /mnt/koji/compose/[release_version]``

Syncing the Compose
-------------------

We sync the compose to ``/pub/alt/stage`` to enable faster access to new content
for QA and the larger Fedora community.

#. Log into the compose backend

   ::

        $ ssh compose-x86-01.phx2.fedoraproject.org

#. Open a screen session

   ::

        $ screen

#. Check the status of the compose

   ::

        $  cat /mnt/koji/compose/[release_version]/[compose_id]/STATUS

   Do not continue with any further steps if the output above is ``DOOMED``.

#. Create the directory targeted for the copy
   ::

        $ sudo -u ftpsync mkdir -p /pub/alt/stage/[release_version]_[release_label]-[#.#]

#. Locate the compose directory that will be the copy source
   ::

        $ ls /mnt/koji/compose/[release_version]/[compose_id]

   .. note::
      Take care executing the synchronization if the next compose
      is already running. Be sure to grab the correct directory.

      If in doubt, check /mnt/koji/compose/[release_version]/[compose_id]/STATUS
      to be sure it is finished.

#. Run the synchronization one-liner

   The synchronization of the completed compose to the public domain is currently
   a one-liner shell script.  Pay close attention to what needs replaced in the example
   below.

   ::

        $ for dir in Everything Cloud CloudImages Docker Labs Server Spins Workstation WorkstationOstree metadata; do sudo -u ftpsync rsync -avhH /mnt/koji/compose/26/Fedora-26-20170328.0/compose/$dir/ /pub/alt/stage/26_Alpha-1.4/$dir/ --link-dest=/pub/fedora/linux/development/26/Everything/ --link-dest=/pub/alt/stage/26_Alpha-1.1/Everything/ --link-dest=/pub/alt/stage/26_Alpha-1.2/Everything/ --link-dest=/pub/alt/stage/26_Alpha-1.3/Everything --link-dest=/pub/alt/stage/26_Alpha-1.4/Everything; done

   .. note::
      This one-liner prompts for the password+token several times over the course of its runtime. If the
      login window is missed it will skip an entire variant.  Just check the source and destination after
      completion and, if there is a directory missing, run the script again.

#. Update the issue in the releng pagure repository

   Once the compose and sync is complete the issue in pagure should be updated and closed.

   .. admonition:: Standard Ticket Verbage

      Compose is done and available from https://kojipkgs.fedoraproject.org/compose/26/Fedora-26-20170328.0/compose/ it has been synced to http://dl.fedoraproject.org/pub/alt/stage/26_Alpha-1.4/ rpms have all be hardlinked to /pub/fedora/linux/development/26/

Verification
============

The method for verifying a compose has completed is checking ``/mnt/koji/compose/[release_version]/[compose_dir]/STATUS``.
Any status other than DOOMED is OK.

Consider before Running
=======================
Composes and file synchronizations should be run in a screen session on a remote machine. This enables the
operator to withstand network connection issues.

.. _pungi-fedora repository:
    https://pagure.io/pungi-fedora

