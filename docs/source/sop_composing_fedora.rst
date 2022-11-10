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
Beta            fedora-beta.conf      release-candidate.sh
GA              fedora-final.conf     release-candidate.sh
=============== ===================== =======================

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
      The very first run of an Beta, or GA compose should have no builds
      listed under the compose tag. It is important to clear pre-existing builds
      from the compose tag when moving between the Beta and RC composes.
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
   ``compose-x86-01.iad2.fedoraproject.org``.

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

        $ sudo ./release-candidate.sh [Beta|RC]-#.#

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

        $ ssh compose-x86-01.iad2.fedoraproject.org

#. Open a screen session

   ::

        $ screen

#. Check the status of the compose

   ::

        $  cat /mnt/koji/compose/[release_version]/[compose_id]/STATUS

   Do not continue with any further steps if the output above is ``DOOMED``.

#. Create the directory targeted for the copy
   ::

        $ sudo -u ftpsync mkdir -m 750 -p /pub/alt/stage/[release_version]_[release_label]-[#.#]

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

        $ sudo -u ftpsync sh -c 'for dir in Everything Cloud Container Kinoite Labs Modular Server Silverblue Spins Workstation metadata; do rsync -avhH /mnt/koji/compose/31/Fedora-31-20190911.0/compose/$dir/ /pub/alt/stage/31_Beta-1.1/$dir/ --link-dest=/pub/fedora/linux/development/31/Everything/ --link-dest=/pub/alt/stage/31_Beta-1.1/Everything/; done'

   .. note::
      If multiple composes are run like 1.2, 1.3, add multiple --link-dest arguments above with multiple composes

#. Set the permissions of the synced compose
   ::

        $ sudo -u ftpsync chmod 755 /pub/alt/stage/[release_version]_[release_label]-[#.#]

#. Update the issue in the releng pagure repository

   Once the compose and sync is complete the issue in pagure should be updated and closed.

   .. admonition:: Standard Ticket Verbage

      Compose is done and available from https://kojipkgs.fedoraproject.org/compose/26/Fedora-26-20170328.0/compose/ it has been synced to http://dl.fedoraproject.org/pub/alt/stage/26_Alpha-1.4/ rpms have all be hardlinked to /pub/fedora/linux/development/26/

Verification
^^^^^^^^^^^^

The method for verifying a compose has completed is checking ``/mnt/koji/compose/[release_version]/[compose_dir]/STATUS``.
Any status other than DOOMED is OK.

Pre-Release Work
================

Pushing Updates to Stable
-------------------------

When the release is signed off on Thursday after the Go/No-Go meeting, push the freeze and blocker to stable updates

Generally the updates are requested stable by QA. If they are not available, you can request them by following

::

   $ bodhi updates request <updateid> stable

Once the updates are requested stable, please push them to stable by following the `bodhi push to stable sop`_

koji tag changes
----------------

Once the updates are pushed stable, we need to clone the koji tag for beta release or lock the koji tag for final release.

For Beta Release
^^^^^^^^^^^^^^^^

::

   $ koji clone-tag --all --latest-only f31 f31-Beta
   $ koji clone-tag --all --latest-only f31-modular f31-Beta-modular

For Final Release
^^^^^^^^^^^^^^^^^

::

   $ koji edit-tag --lock f31
   $ koji edit-tag --lock f31-modular

Bodhi Changes
-------------

Set the bodhi release to ``current``

::

   $ bodhi releases edit --name F31 --state current

Changes for Final Release
=========================

Once Final is GO, we need to perform different changes as that of Beta release.

Last Branched Compose
---------------------

Manually run a branched compose so that the GOLD content is same as the nightly compose.
This also helps in updating the silverblue refs as that of the GOLD content.

Update silverblue refs
----------------------

Please update the refs as per the following commands on `bodhi-backend01.phx2.fedoraproject.org`

Run the following commands from `/mnt/koji/compose/ostree/repo` and `/mnt/koji/ostree/repo/`

::

   $ sudo -u ftpsync ostree refs --create=fedora/31/x86_64/updates/silverblue  fedora/31/x86_64/silverblue
   $ sudo -u ftpsync ostree refs --create=fedora/31/aarch64/updates/silverblue fedora/31/aarch64/silverblue
   $ sudo -u ftpsync ostree refs --create=fedora/31/ppc64le/updates/silverblue fedora/31/ppc64le/silverblue

   $ sudo ostree refs --delete fedora/31/x86_64/silverblue
   $ sudo ostree refs --delete fedora/31/aarch64/silverblue
   $ sudo ostree refs --delete fedora/31/ppc64le/silverblue

   $ sudo -u ftpsync ostree refs --alias --create=fedora/31/x86_64/silverblue  fedora/31/x86_64/updates/silverblue
   $ sudo -u ftpsync ostree refs --alias --create=fedora/31/aarch64/silverblue fedora/31/aarch64/updates/silverblue
   $ sudo -u ftpsync ostree refs --alias --create=fedora/31/ppc64le/silverblue fedora/31/ppc64le/updates/silverblue

Run the following command only from `/mnt/koji/ostree/repo/`

::

   $ sudo ostree summary -u

.. note::
   Before pushing the updates to fxx-updates, run the last branched compose so that both branched and rc composes have the same content.
   Once the branched compose is done, then update the silverblue refs as mentioned above.
   If the order is changed, that will screw up the refs


Disable Branched Compose
------------------------

Now that we have a final GOLD compose, we dont need nightly branched composes anymore.
This is disabled in `releng role`_ in infra ansible repo and then running the playbook.

::

   $ sudo rbac-playbook groups/releng-compose.yml


Lift RelEng freeze
------------------

Lift the RelEng Freeze so that the updates will be pushed to stable.
This is done by editing `RelEngFrozen variable`_ in infra ansible repo and then run the bodhi playbook.

::

   $ sudo rbac-playbook groups/bodhi-backend.yml

Other Changes
-------------

These changes include enabling nightly container and cloud composes, other variable changes in infra ansible repo,
bodhi pungi config changes, updates sync changes and others.

Run the appropriate playbooks after the following changes

::

   diff --git a/roles/releng/files/branched b/roles/releng/files/branched
    index 966f5c3..1c0454f 100644
    --- a/roles/releng/files/branched
    +++ b/roles/releng/files/branched
    @@ -1,3 +1,3 @@
     # branched compose
    -MAILTO=releng-cron@lists.fedoraproject.org
    -15 7 * * * root TMPDIR=`mktemp -d /tmp/branched.XXXXXX` && cd $TMPDIR && git clone https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f31 && /usr/local/bin/lock-wrapper branched-compose "PYTHONMALLOC=debug LANG=en_US.UTF-8 ./nightly.sh" && sudo -u ftpsync /usr/local/bin/update-fullfiletimelist -l /pub/fedora-secondary/update-fullfiletimelist.lock -t /pub fedora fedora-secondary
    +#MAILTO=releng-cron@lists.fedoraproject.org
    +#15 7 * * * root TMPDIR=`mktemp -d /tmp/branched.XXXXXX` && cd $TMPDIR && git clone https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f31 && /usr/local/bin/lock-wrapper branched-compose "PYTHONMALLOC=debug LANG=en_US.UTF-8 ./nightly.sh" && sudo -u ftpsync /usr/local/bin/update-fullfiletimelist -l /pub/fedora-secondary/update-fullfiletimelist.lock -t /pub fedora fedora-secondary
    diff --git a/roles/releng/files/cloud-updates b/roles/releng/files/cloud-updates
    index a0ffbe8..287d57d 100644
    --- a/roles/releng/files/cloud-updates
    +++ b/roles/releng/files/cloud-updates
    @@ -6,6 +6,6 @@ MAILTO=releng-cron@lists.fedoraproject.org
     MAILTO=releng-cron@lists.fedoraproject.org
     15 7 * * * root TMPDIR=`mktemp -d /tmp/CloudF29.XXXXXX` && pushd $TMPDIR && git clone -n https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f29 && LANG=en_US.UTF-8 ./cloud-nightly.sh RC-$(date "+\%Y\%m\%d").0 && popd && rm -rf $TMPDIR
     
    -#Fedora 28 Cloud nightly compose
    -#MAILTO=releng-cron@lists.fedoraproject.org
    -#15 8 * * * root TMPDIR=`mktemp -d /tmp/CloudF28.XXXXXX` && pushd $TMPDIR && git clone -n https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f28 && LANG=en_US.UTF-8 ./cloud-nightly.sh RC-$(date "+\%Y\%m\%d").0 && popd && rm -rf $TMPDIR
    +#Fedora 31 Cloud nightly compose
    +MAILTO=releng-cron@lists.fedoraproject.org
    +15 8 * * * root TMPDIR=`mktemp -d /tmp/CloudF31.XXXXXX` && pushd $TMPDIR && git clone -n https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f31 && LANG=en_US.UTF-8 ./cloud-nightly.sh RC-$(date "+\%Y\%m\%d").0 && popd && rm -rf $TMPDIR
    diff --git a/roles/releng/files/container-updates b/roles/releng/files/container-updates
    index d763149..5446840 100644
    --- a/roles/releng/files/container-updates
    +++ b/roles/releng/files/container-updates
    @@ -1,6 +1,6 @@
    -#Fedora 28 Container Updates nightly compose
    -#MAILTO=releng-cron@lists.fedoraproject.org
    -#45 5 * * * root TMPDIR=`mktemp -d /tmp/containerF28.XXXXXX` && pushd $TMPDIR && git clone -n https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f28 && LANG=en_US.UTF-8 ./container-nightly.sh RC-$(date "+\%Y\%m\%d").0 && popd && rm -rf $TMPDIR
    +#Fedora 31 Container Updates nightly compose
    +MAILTO=releng-cron@lists.fedoraproject.org
    +45 5 * * * root TMPDIR=`mktemp -d /tmp/containerF31.XXXXXX` && pushd $TMPDIR && git clone -n https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f31 && LANG=en_US.UTF-8 ./container-nightly.sh RC-$(date "+\%Y\%m\%d").0 && popd && rm -rf $TMPDIR
     
     # Fedora 30 Container Updates nightly compose
     MAILTO=releng-cron@lists.fedoraproject.org
    diff --git a/vars/all/00-FedoraCycleNumber.yaml b/vars/all/00-FedoraCycleNumber.yaml
    index 22476b0..4bd0d46 100644
    --- a/vars/all/00-FedoraCycleNumber.yaml
    +++ b/vars/all/00-FedoraCycleNumber.yaml
    @@ -1 +1 @@
    -FedoraCycleNumber: 30
    +FedoraCycleNumber: 31

    diff --git a/vars/all/FedoraBranched.yaml b/vars/all/FedoraBranched.yaml
    index 42ac534..0bbcc1d 100644
    --- a/vars/all/FedoraBranched.yaml
    +++ b/vars/all/FedoraBranched.yaml
    @@ -1 +1 @@
    -FedoraBranched: True 
    +FedoraBranched: False 

    diff --git a/vars/all/FedoraPreviousPrevious.yaml b/vars/all/FedoraPreviousPrevious.yaml
    index a8e3d3b..a061e04 100644
    --- a/vars/all/FedoraPreviousPrevious.yaml
    +++ b/vars/all/FedoraPreviousPrevious.yaml
    @@ -1 +1 @@
    -FedoraPreviousPrevious: False
    +FedoraPreviousPrevious: True 
    diff --git a/vars/all/Frozen.yaml b/vars/all/Frozen.yaml
    index 97d3bc3..7578a88 100644
    --- a/vars/all/Frozen.yaml
    +++ b/vars/all/Frozen.yaml
    @@ -1 +1 @@
    -Frozen: True
    +Frozen: False 
    
    
    diff --git a/roles/bodhi2/backend/templates/pungi.rpm.conf.j2 b/roles/bodhi2/backend/templates/pungi.rpm.conf.j2
    index 688bade..28b524a 100644
    --- a/roles/bodhi2/backend/templates/pungi.rpm.conf.j2
    +++ b/roles/bodhi2/backend/templates/pungi.rpm.conf.j2
    @@ -179,8 +179,8 @@ ostree = {
                         # In the case of testing, also inject the last stable updates
                         "https://kojipkgs{{ env_suffix }}.fedoraproject.org/compose/updates/f[[ release.version_int ]]-updates/compose/Everything/$basearch/os/",
                     [% endif %]
    -                # For f31 the compose location is going to be under /compose/branched/
    -                [% if release.version_int == 31 %]
    +                # For F32 the compose location is going to be under /compose/branched/
    +                [% if release.version_int == 32 %]
                         "https://kojipkgs{{ env_suffix }}.fedoraproject.org/compose/branched/latest-Fedora-[[ release.version_int ]]/compose/Everything/$basearch/os/"
                     [% else %]
                         "https://kojipkgs{{ env_suffix }}.fedoraproject.org/compose/[[ release.version_int ]]/latest-Fedora-[[ release.version_int ]]/compose/Everything/$basearch/os/"
    
    diff --git a/roles/bodhi2/backend/templates/pungi.rpm.conf.j2 b/roles/bodhi2/backend/templates/pungi.rpm.conf.j2
    index 28b524a..640ddf0 100644
    --- a/roles/bodhi2/backend/templates/pungi.rpm.conf.j2
    +++ b/roles/bodhi2/backend/templates/pungi.rpm.conf.j2
    @@ -193,8 +193,8 @@ ostree = {
                     "ostree_ref": "fedora/[[ release.version_int ]]/${basearch}/testing/silverblue",
                 [% endif %]
                 "tag_ref": False,
    -            "arches": ["x86_64"],
    -            "failable": ["x86_64"]
    +            "arches": ["x86_64", "ppc64le", "aarch64" ],
    +            "failable": ["x86_64", "ppc64le", "aarch64" ]
             },
         ]
     }
    
    
    diff --git a/roles/bodhi2/backend/files/new-updates-sync b/roles/bodhi2/backend/files/new-updates-sync
    index d08c893..2d0fb4d 100755
    --- a/roles/bodhi2/backend/files/new-updates-sync
    +++ b/roles/bodhi2/backend/files/new-updates-sync
    @@ -25,8 +25,9 @@ RELEASES = {'f31': {'topic': 'fedora',
                         'modules': ['fedora', 'fedora-secondary'],
                         'repos': {'updates': {
                             'from': 'f31-updates',
    -                        'ostrees': [{'ref': 'fedora/31/x86_64/updates/silverblue',
    -                                     'dest': OSTREEDEST}],
    +                        'ostrees': [{'ref': 'fedora/31/%(arch)s/updates/silverblue',
    +                                     'dest': OSTREEDEST,
    +                                     'arches': ['x86_64', 'ppc64le', 'aarch64']}],
                             'to': [{'arches': ['x86_64', 'armhfp', 'aarch64', 'source'],
                                     'dest': os.path.join(FEDORADEST, '31', 'Everything')},
                                    {'arches': ['ppc64le', 's390x'],
    @@ -34,8 +35,9 @@ RELEASES = {'f31': {'topic': 'fedora',
                                   ]},
                                   'updates-testing': {
                             'from': 'f31-updates-testing',
    -                        'ostrees': [{'ref': 'fedora/31/x86_64/testing/silverblue',
    -                                     'dest': OSTREEDEST}],
    +                        'ostrees': [{'ref': 'fedora/31/%(arch)s/testing/silverblue',
    +                                     'dest': OSTREEDEST,
    +                                     'arches': ['x86_64', 'ppc64le', 'aarch64']}],
                             'to': [{'arches': ['x86_64', 'aarch64', 'armhfp', 'source'],
                                     'dest': os.path.join(FEDORADEST, 'testing', '31', 'Everything')},
                                    {'arches': ['ppc64le', 's390x'],
    
    
    diff --git a/roles/pkgdb-proxy/files/pkgdb-gnome-software-collections.json b/roles/pkgdb-proxy/files/pkgdb-gnome-software-collections.json
    index aac977e..9e0cbf2 100644
    --- a/roles/pkgdb-proxy/files/pkgdb-gnome-software-collections.json
    +++ b/roles/pkgdb-proxy/files/pkgdb-gnome-software-collections.json
    @@ -12,14 +12,14 @@
           "version": "devel"
         },
         {
    -      "allow_retire": true,
    +      "allow_retire": false,
           "branchname": "f31",
           "date_created": "2014-05-14 12:36:15",
           "date_updated": "2018-08-14 17:07:23",
           "dist_tag": ".fc31",
           "koji_name": "f31",
           "name": "Fedora",
    -      "status": "Under Development",
    +      "status": "Active",
           "version": "31"
         },
         {

Bodhi config
------------

After Beta
----------
::

    diff --git a/vars/all/FedoraBranchedBodhi.yaml b/vars/all/FedoraBranchedBodhi.yaml
    index 606eb2e..ca2ba61 100644
    --- a/vars/all/FedoraBranchedBodhi.yaml
    +++ b/vars/all/FedoraBranchedBodhi.yaml
    @@ -3,4 +3,4 @@
    #prebeta: After bodhi enablement/beta freeze and before beta release
    #postbeta: After beta release and before final release
    #current: After final release
    -FedoraBranchedBodhi: prebeta
    +FedoraBranchedBodhi: postbeta

After Final
-----------
::

    diff --git a/vars/all/FedoraBranchedBodhi.yaml b/vars/all/FedoraBranchedBodhi.yaml
    index 380f61d..76ba14d 100644
    --- a/vars/all/FedoraBranchedBodhi.yaml
    +++ b/vars/all/FedoraBranchedBodhi.yaml
    @@ -1,2 +1,2 @@
    #options are: prebeta, postbeta, current
    -FedoraBranchedBodhi: postbeta 
    +FedoraBranchedBodhi: current 


Mirroring
---------

Run `stage-release.sh` script from `releng repo`_ in pagure on `bodhi-backend01.phx2.fedoraproject.org`, this will sign the checksums
and will put the content on mirrors.

For Beta
^^^^^^^^

::

   $ sh scripts/stage-release.sh 32_Beta Fedora-32-20200312.0 32_Beta-1.2 fedora-32 1

For Final
^^^^^^^^^

::

   $ sh scripts/stage-release.sh 32 Fedora-32-20200415.0 32_RC-1.1 fedora-32 0

.. note::
   Make sure to grab the directory size usage numbers which is used to send an email to `mirror-admin@lists.fedoraproject.org` list.


Sync the signed checksums to stage
----------------------------------

We need to sync the signed checksums to /pub/alt/stage/ by running the following command

::

   $ for dir in Everything Cloud CloudImages Docker Labs Server Spins Workstation WorkstationOstree metadata; do sudo -u ftpsync rsync -avhH /mnt/koji/compose/26/Fedora-26-20170328.0/compose/$dir/ /pub/alt/stage/26_Alpha-1.4/$dir/ --link-dest=/pub/fedora/linux/development/26/Everything/ --link-dest=/pub/alt/stage/26_Alpha-1.1/Everything/ --link-dest=/pub/alt/stage/26_Alpha-1.2/Everything/ --link-dest=/pub/alt/stage/26_Alpha-1.3/Everything --link-dest=/pub/alt/stage/26_Alpha-1.4/Everything; done

Move development to release folder with mirrormanager
=====================================================

Two weeks after the release move bits from development to release directory

#. ssh to the mm-backend01.iad2.fedoraproject.org
      ::
         $ ssh mm-backend01.iad2.fedoraproject.org

#. get root
      ::
         $ sudo su

#. run the mm2_move-devel-to-release
      ::
         $ mm2_move-devel-to-release --version=35 --category='Fedora Linux'


Consider before Running
=======================
Composes and file synchronizations should be run in a screen session on a remote machine. This enables the
operator to withstand network connection issues.

.. _pungi-fedora repository:
    https://pagure.io/pungi-fedora
.. _bodhi push to stable sop:
   https://docs.pagure.org/releng/sop_pushing_updates.html#pushing-stable-updates-during-freeze
.. _RelEngFrozen variable:
   https://infrastructure.fedoraproject.org/cgit/ansible.git/tree/vars/all/RelEngFrozen.yaml
.. _releng role:
   https://infrastructure.fedoraproject.org/cgit/ansible.git/tree/roles/releng
.. _releng repo:
   https://pagure.io/releng

