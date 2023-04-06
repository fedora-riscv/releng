.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========
End Of Life
===========

Description
===========
Each release of Fedora is maintained as laid out in the `maintenance schedule`_.
At the conclusion of the maintenance period, a Fedora release enters ``end of life`` status.
This procedure describes the tasks necessary to move a release to that status.

Actions
=======

Set date
--------
* Releng responsibilities:
    * Follow guidelines of `maintenance schedule`_
    * Take into account any infrastructure or other supporting project resource
      contention
    * Announce the closure of the release to the package maintainers.

Reminder announcement
---------------------
Send an email to devel@, devel-announce@, test-announce@, announce@ lists as remainder about the release EOL.

Announcement Content
^^^^^^^^^^^^^^^^^^^^
::

  Hello all,

  Fedora 31 will go end of life for updates and support on 24th of
  November 2020. No further updates, including security updates, will be
  available for Fedora 31 after the said date. All the updates of Fedora
  31 being pushed to stable will be stopped as well.

  Fedora 32 will continue to receive updates until approximately one
  month after the release of Fedora 34. The maintenance schedule of
  Fedora releases is documented on the Fedora Project wiki [0]. The
  fedora Project wiki also contains instructions [1] on how to upgrade
  from a previous release of Fedora to a version receiving updates.

  Regards,
  Mohan Boddu.

  [0]https://fedoraproject.org/wiki/Fedora_Release_Life_Cycle#Maintenance_Schedule
  [1]https://fedoraproject.org/wiki/Upgrading?rd=DistributionUpgrades


Koji tasks
----------
* Disable builds by removing targets

::

  $ koji remove-target f31
  $ koji remove-target f31-candidate
  $ koji remove-target f31-container-candidate
  $ koji remove-target f31-flatpak-candidate
  $ koji remove-target f31-infra
  $ koji remove-target f31-coreos-continuous
  $ koji remove-target f31-rebuild
  $ koji remote-target <side-targets> #any side targets that are still around

* Purge from disk the signed copies of rpms that are signed with the EOL'd
  release key.
  To acheive this, add the release key to **koji_cleanup_signed.py** script in `releng`_ repo and the script on compose-branched01.iad2.fedoraproject.org

::

  ./scripts/koji_cleanup_signed.py

PDC tasks
---------
* Set PDC **active** value for the release to **False**

::

  curl -u: -H 'Authorization: Token <token>' -H 'Accept: application/json' -H 'Content-Type:application/json' -X PATCH -d '{"active":"false"}' https://pdc.fedoraproject.org/rest_api/v1/releases/fedora-31/

* Set the EOL dates in PDC for all the components to the release EOL date if they are not already set.
  Run the following script from `releng`_ repo

::

  python scripts/pdc/adjust-eol-all.py <token> f31 2020-11-24

Bodhi tasks
-----------
* Run the following bodhi commands to set the releases state to **archived**

::

  $ bodhi releases edit --name "F31" --state archived
  $ bodhi releases edit --name "F31M" --state archived
  $ bodhi releases edit --name "F31C" --state archived
  $ bodhi releases edit --name "F31F" --state archived

.. warning::
  Due to a `bug <https://github.com/fedora-infra/bodhi/issues/2177>`_ in Bodhi, it is
  critical that Bodhi processes be restarted any time ``bodhi releases create`` or
  ``bodhi releases edit`` are used.

* On bodhi-backend01.iad2.fedoraproject.org, run the following commands

::

  $ sudo systemctl restart fm-consumer@config.service
  $ sudo systemctl restart bodhi-celery.service

Fedora Infra Ansible Changes
----------------------------

* We need to make changes to bodhi, koji, mbs, releng, autosign roles in ansible repo.

.. code-block:: diff

  From 73dc8a1042a190f1b88bf78e110d44753cfa7962 Mon Sep 17 00:00:00 2001
  From: Mohan Boddu <mboddu@bhujji.com>
  Date: Nov 24 2020 17:19:23 +0000
  Subject: F31 EOL


  Signed-off-by: Mohan Boddu <mboddu@bhujji.com>

  ---

  diff --git a/roles/bodhi2/backend/files/new-updates-sync b/roles/bodhi2/backend/files/new-updates-sync
  index a143047..d8c8a73 100755
  --- a/roles/bodhi2/backend/files/new-updates-sync
  +++ b/roles/bodhi2/backend/files/new-updates-sync
  @@ -113,50 +113,6 @@ RELEASES = {'f33': {'topic': 'fedora',
                                  'dest': os.path.join(FEDORAALTDEST, 'testing', '32', 'Modular')}
                                ]}}
                      },
  -            'f31': {'topic': 'fedora',
  -                    'version': '31',
  -                    'modules': ['fedora', 'fedora-secondary'],
  -                    'repos': {'updates': {
  -                        'from': 'f31-updates',
  -                        'ostrees': [{'ref': 'fedora/31/%(arch)s/updates/silverblue',
  -                                     'dest': OSTREEDEST,
  -                                     'arches': ['x86_64', 'ppc64le', 'aarch64']}],
  -                        'to': [{'arches': ['x86_64', 'armhfp', 'aarch64', 'source'],
  -                                'dest': os.path.join(FEDORADEST, '31', 'Everything')},
  -                               {'arches': ['ppc64le', 's390x'],
  -                                'dest': os.path.join(FEDORAALTDEST, '31', 'Everything')}
  -                              ]},
  -                              'updates-testing': {
  -                        'from': 'f31-updates-testing',
  -                        'ostrees': [{'ref': 'fedora/31/%(arch)s/testing/silverblue',
  -                                     'dest': OSTREEDEST,
  -                                     'arches': ['x86_64', 'ppc64le', 'aarch64']}],
  -                        'to': [{'arches': ['x86_64', 'aarch64', 'armhfp', 'source'],
  -                                'dest': os.path.join(FEDORADEST, 'testing', '31', 'Everything')},
  -                               {'arches': ['ppc64le', 's390x'],
  -                                'dest': os.path.join(FEDORAALTDEST, 'testing', '31', 'Everything')}
  -                              ]}}
  -                   },
  -            'f31m': {'topic': 'fedora',
  -                    'version': '31m',
  -                    'modules': ['fedora', 'fedora-secondary'],
  -                    'repos': {'updates': {
  -                        'from': 'f31-modular-updates',
  -                        'ostrees': [],
  -                        'to': [{'arches': ['x86_64', 'aarch64', 'armhfp', 'source'],
  -                                'dest': os.path.join(FEDORADEST, '31', 'Modular')},
  -                               {'arches': ['ppc64le', 's390x'],
  -                                'dest': os.path.join(FEDORAALTDEST, '31', 'Modular')}
  -                              ]},
  -                              'updates-testing': {
  -                        'from': 'f31-modular-updates-testing',
  -                        'ostrees': [],
  -                        'to': [{'arches': ['x86_64', 'aarch64', 'armhfp', 'source'],
  -                                'dest': os.path.join(FEDORADEST, 'testing', '31', 'Modular')},
  -                               {'arches': ['ppc64le', 's390x'],
  -                                'dest': os.path.join(FEDORAALTDEST, 'testing', '31', 'Modular')}
  -                              ]}}
  -                   },
              'epel8': {'topic': 'epel',
                        'version': '8',
                        'modules': ['epel'],
  diff --git a/roles/bodhi2/backend/tasks/main.yml b/roles/bodhi2/backend/tasks/main.yml
  index a4b2a2b..d84f86a 100644
  --- a/roles/bodhi2/backend/tasks/main.yml
  +++ b/roles/bodhi2/backend/tasks/main.yml
  @@ -76,7 +76,7 @@
    # bodhi2/backend/files/koji_sync_listener.py
    # This cronjob runs only once a day.  The listener script runs reactively.
    cron: name="owner-sync" minute="15" hour="4" user="root"
  -      job="/usr/local/bin/lock-wrapper owner-sync '/usr/local/bin/owner-sync-pagure f34 f34-container f34-modular f33 f33-container f33-modular f33-flatpak f32 f32-container f32-modular f32-flatpak f31 f31-container f31-flatpak f31-modular epel8 epel8-playground epel8-modular epel7 dist-6E-epel module-package-list modular'"
  +      job="/usr/local/bin/lock-wrapper owner-sync '/usr/local/bin/owner-sync-pagure f34 f34-container f34-modular f33 f33-container f33-modular f33-flatpak f32 f32-container f32-modular f32-flatpak epel8 epel8-playground epel8-modular epel7 dist-6E-epel module-package-list modular'"
        cron_file=update-koji-owner
    when: env == "production"
    tags:
  diff --git a/roles/bodhi2/backend/templates/koji_sync_listener.toml b/roles/bodhi2/backend/templates/koji_sync_listener.toml
  index 753adc0..41954ca 100644
  --- a/roles/bodhi2/backend/templates/koji_sync_listener.toml
  +++ b/roles/bodhi2/backend/templates/koji_sync_listener.toml
  @@ -48,10 +48,6 @@ taglist = [
      "f32-container",
      "f32-modular",
      "f32-flatpak",
  -    "f31",
  -    "f31-container",
  -    "f31-flatpak",
  -    "f31-modular",
      "epel8",
      "epel8-playground",
      "epel8-modular",
  diff --git a/roles/koji_hub/templates/hub.conf.j2 b/roles/koji_hub/templates/hub.conf.j2
  index 2f8b716..4816dba 100644
  --- a/roles/koji_hub/templates/hub.conf.j2
  +++ b/roles/koji_hub/templates/hub.conf.j2
  @@ -187,6 +187,5 @@ sidetag =
      tag f34-build :: allow
      tag f33-build :: allow
      tag f32-build :: allow
  -    tag f31-build :: allow
      tag eln-build :: allow
      all :: deny
  diff --git a/roles/mbs/common/files/default-modules.production/platform-f31.yaml b/roles/mbs/common/files/default-modules.production/platform-f31.yaml
  deleted file mode 100644
  index 0608f93..0000000
  --- a/roles/mbs/common/files/default-modules.production/platform-f31.yaml
  +++ /dev/null
  @@ -1,28 +0,0 @@
  -data:
  -  description: Fedora 31 traditional base
  -  license:
  -    module: [MIT]
  -  name: platform
  -  profiles:
  -    buildroot:
  -      rpms: [bash, bzip2, coreutils, cpio, diffutils, fedora-release, findutils, gawk,
  -        glibc-minimal-langpack, grep, gzip, info, make, patch, redhat-rpm-config,
  -        rpm-build, sed, shadow-utils, tar, unzip, util-linux, which, xz]
  -    srpm-buildroot:
  -      rpms: [bash, fedora-release, fedpkg-minimal, glibc-minimal-langpack, gnupg2,
  -        redhat-rpm-config, rpm-build, shadow-utils]
  -  stream: f31
  -  summary: Fedora 31 traditional base
  -  context: 00000000
  -  version: 1
  -  xmd:
  -    mbs:
  -      buildrequires: {}
  -      commit: f31
  -      requires: {}
  -      koji_tag: module-f31-build
  -      mse: TRUE
  -      virtual_streams: [fedora]
  -document: modulemd
  -version: 1
  -
  diff --git a/roles/pkgdb-proxy/files/pkgdb-gnome-software-collections.json b/roles/pkgdb-proxy/files/pkgdb-gnome-software-collections.json
  index d2f9a89..0eae499 100644
  --- a/roles/pkgdb-proxy/files/pkgdb-gnome-software-collections.json
  +++ b/roles/pkgdb-proxy/files/pkgdb-gnome-software-collections.json
  @@ -41,7 +41,7 @@
        "dist_tag": ".fc31",
        "koji_name": "f31",
        "name": "Fedora",
  -      "status": "Active",
  +      "status": "EOL",
        "version": "31"
      },
      {
  diff --git a/roles/releng/files/cloud-updates b/roles/releng/files/cloud-updates
  index 0a37b49..ebb807c 100644
  --- a/roles/releng/files/cloud-updates
  +++ b/roles/releng/files/cloud-updates
  @@ -7,5 +7,5 @@ MAILTO=releng-cron@lists.fedoraproject.org
  15 7 * * * root TMPDIR=`mktemp -d /tmp/CloudF32.XXXXXX` && pushd $TMPDIR && git clone -n https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f32 && LANG=en_US.UTF-8 ./cloud-nightly.sh RC-$(date "+\%Y\%m\%d").0 && popd && rm -rf $TMPDIR
  
  # Fedora 31 Cloud nightly compose
  -MAILTO=releng-cron@lists.fedoraproject.org
  -15 8 * * * root TMPDIR=`mktemp -d /tmp/CloudF31.XXXXXX` && pushd $TMPDIR && git clone -n https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f31 && LANG=en_US.UTF-8 ./cloud-nightly.sh RC-$(date "+\%Y\%m\%d").0 && popd && rm -rf $TMPDIR
  +#MAILTO=releng-cron@lists.fedoraproject.org
  +#15 8 * * * root TMPDIR=`mktemp -d /tmp/CloudF31.XXXXXX` && pushd $TMPDIR && git clone -n https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f31 && LANG=en_US.UTF-8 ./cloud-nightly.sh RC-$(date "+\%Y\%m\%d").0 && popd && rm -rf $TMPDIR
  diff --git a/roles/releng/files/container-updates b/roles/releng/files/container-updates
  index d3a0e14..6932bec 100644
  --- a/roles/releng/files/container-updates
  +++ b/roles/releng/files/container-updates
  @@ -1,6 +1,6 @@
  #Fedora 31 Container Updates nightly compose
  -MAILTO=releng-cron@lists.fedoraproject.org
  -45 5 * * * root TMPDIR=`mktemp -d /tmp/containerF31.XXXXXX` && pushd $TMPDIR && git clone -n https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f31 && LANG=en_US.UTF-8 ./container-nightly.sh RC-$(date "+\%Y\%m\%d").0 && popd && rm -rf $TMPDIR
  +#MAILTO=releng-cron@lists.fedoraproject.org
  +#45 5 * * * root TMPDIR=`mktemp -d /tmp/containerF31.XXXXXX` && pushd $TMPDIR && git clone -n https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f31 && LANG=en_US.UTF-8 ./container-nightly.sh RC-$(date "+\%Y\%m\%d").0 && popd && rm -rf $TMPDIR
  
  # Fedora 33 Container Updates nightly compose
  MAILTO=releng-cron@lists.fedoraproject.org
  diff --git a/roles/robosignatory/templates/robosignatory.toml.j2 b/roles/robosignatory/templates/robosignatory.toml.j2
  index 41ab24c..60295c1 100644
  --- a/roles/robosignatory/templates/robosignatory.toml.j2
  +++ b/roles/robosignatory/templates/robosignatory.toml.j2
  @@ -92,30 +92,6 @@ handlers = ["console"]
  
              # Temporary tags
  
  -            [[consumer_config.koji_instances.primary.tags]]
  -            from = "f31-kde"
  -            to = "f31-kde"
  -            key = "{{ (env == 'production')|ternary('fedora-31', 'testkey') }}"
  -            keyid = "{{ (env == 'production')|ternary('3c3359c4', 'd300e724') }}"
  -
  -            [[consumer_config.koji_instances.primary.tags]]
  -            from = "f31-gnome"
  -            to = "f31-gnome"
  -            key = "{{ (env == 'production')|ternary('fedora-31', 'testkey') }}"
  -            keyid = "{{ (env == 'production')|ternary('3c3359c4', 'd300e724') }}"
  -
  -            [[consumer_config.koji_instances.primary.tags]]
  -            from = "f31-python"
  -            to = "f31-python"
  -            key = "{{ (env == 'production')|ternary('fedora-31', 'testkey') }}"
  -            keyid = "{{ (env == 'production')|ternary('3c3359c4', 'd300e724') }}"
  -
  -            [[consumer_config.koji_instances.primary.tags]]
  -            from = "f30-kde"
  -            to = "f30-kde"
  -            key = "{{ (env == 'production')|ternary('fedora-30', 'testkey') }}"
  -            keyid = "{{ (env == 'production')|ternary('cfc659b9', 'd300e724') }}"
  -
              # Infra tags
  
              [[consumer_config.koji_instances.primary.tags]]
  @@ -143,12 +119,6 @@ handlers = ["console"]
              keyid = "{{ (env == 'production')|ternary('47dd8ef9', 'd300e724') }}"
  
              [[consumer_config.koji_instances.primary.tags]]
  -            from = "f31-infra-candidate"
  -            to = "f31-infra-stg"
  -            key = "{{ (env == 'production')|ternary('fedora-infra', 'testkey') }}"
  -            keyid = "{{ (env == 'production')|ternary('47dd8ef9', 'd300e724') }}"
  -
  -            [[consumer_config.koji_instances.primary.tags]]
              from = "f32-infra-candidate"
              to = "f32-infra-stg"
              key = "{{ (env == 'production')|ternary('fedora-infra', 'testkey') }}"
  @@ -170,18 +140,6 @@ handlers = ["console"]
              # Gated coreos-pool tag
  
              [[consumer_config.koji_instances.primary.tags]]
  -            from = "f30-coreos-signing-pending"
  -            to = "coreos-pool"
  -            key = "{{ (env == 'production')|ternary('fedora-30', 'testkey') }}"
  -            keyid = "{{ (env == 'production')|ternary('cfc659b9', 'd300e724') }}"
  -
  -            [[consumer_config.koji_instances.primary.tags]]
  -            from = "f31-coreos-signing-pending"
  -            to = "coreos-pool"
  -            key = "{{ (env == 'production')|ternary('fedora-31', 'testkey') }}"
  -            keyid = "{{ (env == 'production')|ternary('3c3359c4', 'd300e724') }}"
  -
  -            [[consumer_config.koji_instances.primary.tags]]
              from = "f32-coreos-signing-pending"
              to = "coreos-pool"
              key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
  @@ -297,19 +255,6 @@ handlers = ["console"]
              keyid = "{{ (env == 'production')|ternary('12c944d0', 'd300e724') }}"
              type = "modular"
  
  -            [[consumer_config.koji_instances.primary.tags]]
  -            from = "f31-signing-pending"
  -            to = "f31-updates-testing-pending"
  -            key = "{{ (env == 'production')|ternary('fedora-31', 'testkey') }}"
  -            keyid = "{{ (env == 'production')|ternary('3c3359c4', 'd300e724') }}"
  -
  -            [[consumer_config.koji_instances.primary.tags]]
  -            from = "f31-modular-signing-pending"
  -            to = "f31-modular-updates-testing-pending"
  -            key = "{{ (env == 'production')|ternary('fedora-31', 'testkey') }}"
  -            keyid = "{{ (env == 'production')|ternary('3c3359c4', 'd300e724') }}"
  -            type = "modular"
  -
              #epel8 modular tags
              [[consumer_config.koji_instances.primary.tags]]
              from = "epel8-modular-signing-pending"
  @@ -417,12 +362,6 @@ handlers = ["console"]
              key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
              keyid = "{{ (env == 'production')|ternary('12c944d0', 'd300e724') }}"
  
  -            [[consumer_config.koji_instances.primary.tags]]
  -            from = "f31-openh264"
  -            to = "f31-openh264"
  -            key = "{{ (env == 'production')|ternary('fedora-31', 'testkey') }}"
  -            keyid = "{{ (env == 'production')|ternary('3c3359c4', 'd300e724') }}"
  -
              # f33-rebuild
              [[consumer_config.koji_instances.primary.tags]]
              from = "f33-rebuild"

* Run the associated playbooks on *batcave*

::

  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/groups/bodhi-backend.yml
  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/groups/koji-hub.yml
  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/groups/mbs.yml
  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/groups/releng-compose.yml
  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/groups/proxies -t pkgdb2
  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/manual/autosign.yml
  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/openshift-apps/bodhi.yml

MBS Platform Retirement
-----------------------
* To retire the platform in mbs, run the following command on mbs-backend01.iad2.fedoraproject.org

::

  $ sudo mbs-manager retire platform:f31

Final announcement
------------------

* Send the final announcement to devel@, devel-announce@, test-announce@, announce@ lists

Announcement content
^^^^^^^^^^^^^^^^^^^^
::

  Hello all,

  As of the 24th of November 2020, Fedora 31 has reached its end of life
  for updates and support. No further updates, including security
  updates, will be available for Fedora 31. All the updates that are
  currently in testing won't get pushed to stable. Fedora 32 will
  continue to receive updates until approximately one month after the
  release of Fedora 34. The maintenance schedule of Fedora releases is
  documented on the Fedora Project wiki [0]. The Fedora Project wiki
  also contains instructions [1] on how to upgrade from a previous
  release of Fedora to a version receiving updates.

  Mohan Boddu.

  [0] https://fedoraproject.org/wiki/Fedora_Release_Life_Cycle#Maintenance_Schedule
  [1] https://docs.fedoraproject.org/en-US/quick-docs/dnf-system-upgrade/

Update eol wiki page
^^^^^^^^^^^^^^^^^^^^

https://fedoraproject.org/wiki/End_of_life update with release and number of
days.

Move the EOL release to archive
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#. log into to bodhi-backend01 and become root

    ::

      $ ssh bodhi-backend01.iad2.fedoraproject.org
      $ sudo su
      $ su - ftpsync  
  
#. then change into the releases directory.

    ::

      $ cd /pub/fedora/linux/releases

#. check to see that the target directory doesnt already exist.

    ::

      $ ls /pub/archive/fedora/linux/releases/
  
#. do a recursive rsync to update any changes in the trees since the previous copy.

    ::

      $ rsync -avAXSHP ./35/ /pub/archive/fedora/linux/releases/35/
  
#. we now do the updates and updates/testing in similar ways.

    ::

      $ cd ../updates/
      $ rsync -avAXSHP 35/ /pub/archive/fedora/linux/updates/35/
      $ cd testing
      $ rsync -avAXSHP 35/ /pub/archive/fedora/linux/updates/testing/35/
  
#. do the same with fedora-secondary.
#. announce to the mirror list this has been done and that in 2 weeks you will move the old trees to archives.
#. in two weeks, log into mm-backend01 and run the archive script

    ::

      $ sudo -u mirrormanager mm2_move-to-archive --originalCategory="Fedora Linux" --archiveCategory="Fedora Archive" --directoryRe='/35/Everything'

#. if there are problems, the postgres DB may have issues and so you need to get a DBA to update the backend to fix items.
#. wait an hour or so then you can remove the files from the main tree.

    ::

      $ ssh bodhi-backend01
      $ cd /pub/fedora/linux
      $ cd releases/35
      $ ls # make sure you have stuff here
      $ rm -rf *
      $ ln ../20/README .
      $ cd ../../updates/35
      $ ls #make sure you have stuff here
      $ rm -rf *
      $ ln ../20/README .
      $ cd ../testing/35
      $ ls # make sure you have stuff here
      $ rm -rf *
      $ ln ../20/README .


Consider Before Running
=======================
* Resource contention in infrastructure, such as outages
* Extenuating circumstances for specific planned updates, if any
* Send the reminder announcement, if it isn't sent already

.. _maintenance schedule:
    https://fedoraproject.org/wiki/Fedora_Release_Life_Cycle#Maintenance_Schedule
.. _End of Life Process:
    https://fedoraproject.org/wiki/BugZappers/HouseKeeping#End_of_Life_.28EOL.29
.. _cold undead hands:
    https://pagure.io/fedora-badges/blob/master/f/rules/you-can-pry-it-from-my-cold-undead-hands.yml
.. _File Taskotron ticket:
    https://pagure.io/taskotron/new_issue?title=Fedora%20EOL%20notification&content=Fedora%20NN%20is%20now%20EOL
.. _releng:
    https://pagure.io/releng

