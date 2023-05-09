.. SPDX-License-Identifier:    CC-BY-SA-3.0


================
生命周期结束
================

说明
===========
Fedora的每个版本都按照 `维护时间表`_ 中的规定进行维护。在维护期结束时，Fedora版本进入 ``end of life`` 状态。此过程描述了将发布移动到该状态所需的任务。

操作
=======

设置日期
--------
* Releng责任:
    * 遵循 `维护时间表`_
    * 考虑任何基础设施或其他支持项目的资源竞争
    * 向软件包维护人员宣布发布的结束。

提醒公告
---------------------
发送电子邮件至 devel@, devel-announce@, test-announce@, announce@ 列出关于发布EOL的剩余部分。

公告内容
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


Koji任务
----------
* 通过删除目标禁用构建

::

  $ koji remove-target f31
  $ koji remove-target f31-candidate
  $ koji remove-target f31-container-candidate
  $ koji remove-target f31-flatpak-candidate
  $ koji remove-target f31-infra
  $ koji remove-target f31-coreos-continuous
  $ koji remove-target f31-rebuild
  $ koji remote-target <side-targets> #any side targets that are still around

* 从磁盘中清除使用EOL发布密钥签名的rpms的签名副本。要实现这一点，请将发布密钥添加到 `releng`_ 仓库中的 **koji_cleanup_signed.py** 脚本和 compose-branched01.iad2.fedoraproject.org 上的脚本中

::

  ./scripts/koji_cleanup_signed.py

PDC任务
---------
* 将版本的PDC **活跃** 值设置为 **False**

::

  curl -u: -H 'Authorization: Token <token>' -H 'Accept: application/json' -H 'Content-Type:application/json' -X PATCH -d '{"active":"false"}' https://pdc.fedoraproject.org/rest_api/v1/releases/fedora-31/

* 如果尚未设置，则在PDC中将所有组件的EOL日期设置为发布EOL日期。从 `releng`_ 仓库运行以下脚本

::

  python scripts/pdc/adjust-eol-all.py <token> f31 2020-11-24

Bodhi任务
-----------
* 运行以下bodhi命令将版本状态设置为 **archived**

::

  $ bodhi releases edit --name "F31" --state archived
  $ bodhi releases edit --name "F31M" --state archived
  $ bodhi releases edit --name "F31C" --state archived
  $ bodhi releases edit --name "F31F" --state archived

.. warning::
  由于Bodhi中的一个 `bug <https://github.com/fedora-infra/bodhi/issues/2177>`_ ，在使用 ``bodhi releases create`` 或
  ``bodhi releases edit`` 的任何时候都必须重新启动Bodhi进程。

* 在 bodhi-backend01.iad2.fedoraproject.org 上，运行以下命令

::

  $ sudo systemctl restart fm-consumer@config.service
  $ sudo systemctl restart bodhi-celery.service

Fedora Infra Ansible 更改
----------------------------

* 我们需要对ansible repo中的bodhi、koji、mbs、reling和autosign角色进行更改。

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

* 在 *batcave* 上运行相关的playbook

::

  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/groups/bodhi-backend.yml
  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/groups/koji-hub.yml
  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/groups/mbs.yml
  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/groups/releng-compose.yml
  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/groups/proxies -t pkgdb2
  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/manual/autosign.yml
  $ sudo ansible-playbook /srv/web/infra/ansible/playbooks/openshift-apps/bodhi.yml

MBS平台退役
-----------------------
* 要在mbs中退役该平台，请在 mbs-backend01.iad2.fedoraproject.org 上运行以下命令

::

  $ sudo mbs-manager retire platform:f31

最终公告
------------------

* 将最终公告发送到 devel@, devel-announce@, test-announce@, announce@ lists

公告内容
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

更新eol wiki页面
^^^^^^^^^^^^^^^^^^^^

https://fedoraproject.org/wiki/End_of_life 更新版本和天数。

将EOL版本移动到archive
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#. 登录到 bodhi-backend01 并成为root用户

    ::

      $ ssh bodhi-backend01.iad2.fedoraproject.org
      $ sudo su
      $ su - ftpsync  
  
#. 然后切换到版本目录。

    ::

      $ cd /pub/fedora/linux/releases

#. 检查目标目录是否不存在。

    ::

      $ ls /pub/archive/fedora/linux/releases/
  
#. 执行递归rsync以更新自上一次复制以来树中的任何更改。

    ::

      $ rsync -avAXSHP ./35/ /pub/archive/fedora/linux/releases/35/
  
#. 我们现在以类似的方式进行更新和更新/测试。

    ::

      $ cd ../updates/
      $ rsync -avAXSHP 35/ /pub/archive/fedora/linux/updates/35/
      $ cd testing
      $ rsync -avAXSHP 35/ /pub/archive/fedora/linux/updates/testing/35/
  
#. fedora-secondary也是如此。
#. 向镜像列表宣布这已经完成，两周后你将把旧的树移到archives。
#. 两周后，登录 mm-backend01 并运行归档脚本。

    ::

      $ sudo -u mirrormanager mm2_move-to-archive --originalCategory="Fedora Linux" --archiveCategory="Fedora Archive" --directoryRe='/35/Everything'

#. 如果出现问题，postgres数据库可能会出现问题，因此您需要找一个DBA来更新后端以修复项目。
#. 等待一个小时左右，然后可以从主目录树中删除这些文件。

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


运行之前请考虑
=======================
* 基础架构中的资源争用，如停机
* 特定计划更新的情有可原的情况（如有）
* 发送提醒公告（如果尚未发送）

.. _维护时间表:
    https://fedoraproject.org/wiki/Fedora_Release_Life_Cycle#Maintenance_Schedule
.. _End of Life Process:
    https://fedoraproject.org/wiki/BugZappers/HouseKeeping#End_of_Life_.28EOL.29
.. _cold undead hands:
    https://pagure.io/fedora-badges/blob/master/f/rules/you-can-pry-it-from-my-cold-undead-hands.yml
.. _File Taskotron ticket:
    https://pagure.io/taskotron/new_issue?title=Fedora%20EOL%20notification&content=Fedora%20NN%20is%20now%20EOL
.. _releng:
    https://pagure.io/releng

