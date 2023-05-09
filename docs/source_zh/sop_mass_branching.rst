.. SPDX-License-Identifier:    CC-BY-SA-3.0


==============
大规模分支
==============

说明
===========

在每次alpha冻结时，我们将待发布的版本从 ``devel/`` 分支中分离出来，这样rawhide就可以继续前进，同时待发布的版本可以进入漏洞修复和优化模式。

操作
======

更新 fedscm-admin
-------------------

将新版本添加到 fedscm-admin 中，创建一个更新并将其发送到limb。

请查看 `fedscm-admin commit`_.


分支仓库
---------------

以下列出的所有仓库都需要更新，包括为branched版本添加一个新分支，以及使用新的发布值更新rawhide分支。

1. https://pagure.io/pungi-fedora
2. https://pagure.io/fedora-kickstarts
3. https://pagure.io/fedora-comps
4. https://pagure.io/fedora-lorax-templates/
5. https://pagure.io/releng/fedora-module-defaults/
6. https://pagure.io/workstation-ostree-config/
7. https://src.fedoraproject.org/rpms/fedora-release
8. https://src.fedoraproject.org/rpms/fedora-repos

PDC
---

"product-release" 需要在PDC中创建。

在 ``scripts/pdc/`` 目录中，运行::

    $ python create-product-release.py fedora $TOKEN Fedora $NEW_VERSION


在 ``pdc-backend01.stg`` (用于测试) 或 ``pdc-backend01`` (用于生产)
克隆 (或更新现有克隆) releng 仓库::

    git clone https://pagure.io/releng.git


在 ``scripts/pdc/`` 目录中，运行 (有关如何运行脚本的信息，请参阅脚本的 ``--help`` )::

    $ python create-new-release-branches.py ... --createfile


.. note:: ``--createfile`` 参数是必需的，下一步需要该文件。

.. note:: 由于pdc中存在内存泄漏问题，我们需要在
          /etc/pdc.d/fedora.json 中设置配置
          {
          "fedora": {
          "host": "http://pdc-web02.iad2.fedoraproject.org/rest_api/v1/",
          "develop": false,
          "ssl-verify": false,
          }
          }

dist-git
--------

既然pdc有了新版本，并且每个包都在pdc中进行了分支，我们需要分两步更新dist-git：

- 用git创建新分支
- 更新 gitolite.conf 以允许用户推送到此新分支

对于这两个操作，您都需要上面pdc生成的文件。

创建git分支
^^^^^^^^^^^^^^^^^^^^^^^

在 ``pkgs01.stg`` (用于测试) 或 ``pkgs02`` (用于生产)上，运行::

    $ sudo -u pagure python /usr/local/bin/mass-branching-git.py <new branch name> <input file>

其中 ``<new branch name>`` 将类似于 ``f28`` ， ``<input file>`` 是上面pdc生成的文件的路径。


Ansible
-------

ansible中的应用程序需要更新以了解新的分支。

PkgDB
^^^^^

在pkgdb完全退役之前，这是暂时的措施，但与此同时，需要将新版本添加到其中。
为此，请调整 `pkgdb-proxy role`_ 中的infra ansible playbook：

::

    --- a/roles/pkgdb-proxy/files/pkgdb-gnome-software-collections.json
    +++ b/roles/pkgdb-proxy/files/pkgdb-gnome-software-collections.json
    @@ -4,8 +4,8 @@
           "allow_retire": true,
           "branchname": "rawhide",
           "date_created": "2014-05-14 12:36:15",
    -      "date_updated": "2019-08-14 17:07:23",
    -      "dist_tag": ".fc32",
    +      "date_updated": "2020-02-11 17:07:23",
    +      "dist_tag": ".fc33",
           "koji_name": "rawhide",
           "name": "Fedora",
           "status": "Under Development",
    @@ -13,6 +13,17 @@
         },
         {
           "allow_retire": false,
    +      "branchname": "f32",
    +      "date_created": "2014-05-14 12:36:15",
    +      "date_updated": "2020-02-11 17:07:23",
    +      "dist_tag": ".fc32",
    +      "koji_name": "f32",
    +      "name": "Fedora",
    +      "status": "Under Development",
    +      "version": "32"
    +    },
    +    {
    +      "allow_retire": false,
           "branchname": "f31",
           "date_created": "2014-05-14 12:36:15",
           "date_updated": "2018-08-14 17:07:23",

fedora-packages
^^^^^^^^^^^^^^^

fedora-packages 中有一个文件需要用新版本更新。它会告诉告诉包装上哪些标签需要询问koji。和以前一样，进行以下编辑 `packages3 role`_ 中的ansible repo:

::

    --- a/roles/packages3/web/files/distmappings.py
    +++ b/roles/packages3/web/files/distmappings.py
    @@ -1,5 +1,9 @@
     # Global list of koji tags we care about
    -tags = ({'name': 'Rawhide', 'tag': 'f32'},
    +tags = ({'name': 'Rawhide', 'tag': 'f33'},
    +
    +        {'name': 'Fedora 32', 'tag': 'f32-updates'},
    +        {'name': 'Fedora 32', 'tag': 'f32'},
    +        {'name': 'Fedora 32 Testing', 'tag': 'f32-updates-testing'},

             {'name': 'Fedora 31', 'tag': 'f31-updates'},
             {'name': 'Fedora 31', 'tag': 'f31'},

Bodhi
^^^^^

Bodhi 需要更新才能添加新版本。这需要在infra ansible repo中完成 `bodhi2 role`_。
这一变化包括更新 koji-sync-listener.py、new-updates-sync、rpm和modular更新的pungi 配置、bodhi 模板。

::

    --- a/roles/bodhi2/backend/files/koji-sync-listener.py
    +++ b/roles/bodhi2/backend/files/koji-sync-listener.py
    @@ -23,7 +23,7 @@ def handle(content):
         sys.stdout.flush()
         # XXX If you modify this taglist.  Please also modify the other copy in
         # bodhi2/backend/tasks/main.yml
    -    taglist = 'f32 f32-container f32-modular f32-flatpak f31 f31-container f31-flatpak f31-modular f30 f30-container f30-flatpak f30-modular epel8 epel8-playground epel8-modular epel7 dist-6E-epel module-package-list modular'
    +    taglist = 'f33 f33-container f33-modular f33-flatpak f32 f32-container f32-modular f32-flatpak f31 f31-container f31-flatpak f31-modular f30 f30-container f30-flatpak f30-modular epel8 epel8-playground epel8-modular epel7 dist-6E-epel module-package-list modular'
        cmd = [
            '/usr/local/bin/owner-sync-pagure',
            '--package', package,

    diff --git a/roles/bodhi2/backend/files/new-updates-sync b/roles/bodhi2/backend/files/new-updates-sync
    index 2228517..3baa775 100755
    --- a/roles/bodhi2/backend/files/new-updates-sync
    +++ b/roles/bodhi2/backend/files/new-updates-sync
    @@ -20,7 +20,51 @@ FEDORAALTDEST = '/pub/fedora-secondary/updates/'
     EPELDEST = '/pub/epel/'
     OSTREESOURCE = '/mnt/koji/compose/ostree/repo/'
     OSTREEDEST = '/mnt/koji/ostree/repo/'
    -RELEASES = {'f31': {'topic': 'fedora',
    +RELEASES = {'f32': {'topic': 'fedora',
    +                    'version': '32',
    +                    'modules': ['fedora', 'fedora-secondary'],
    +                    'repos': {'updates': {
    +                        'from': 'f32-updates',
    +                        'ostrees': [{'ref': 'fedora/32/%(arch)s/updates/silverblue',
    +                                     'dest': OSTREEDEST,
    +                                     'arches': ['x86_64', 'ppc64le', 'aarch64']}],
    +                        'to': [{'arches': ['x86_64', 'armhfp', 'aarch64', 'source'],
    +                                'dest': os.path.join(FEDORADEST, '32', 'Everything')},
    +                               {'arches': ['ppc64le', 's390x'],
    +                                'dest': os.path.join(FEDORAALTDEST, '32', 'Everything')}
    +                              ]},
    +                              'updates-testing': {
    +                        'from': 'f32-updates-testing',
    +                        'ostrees': [{'ref': 'fedora/32/%(arch)s/testing/silverblue',
    +                                     'dest': OSTREEDEST,
    +                                     'arches': ['x86_64', 'ppc64le', 'aarch64']}],
    +                        'to': [{'arches': ['x86_64', 'aarch64', 'armhfp', 'source'],
    +                                'dest': os.path.join(FEDORADEST, 'testing', '32', 'Everything')},
    +                               {'arches': ['ppc64le', 's390x'],
    +                                'dest': os.path.join(FEDORAALTDEST, 'testing', '32', 'Everything')}
    +                              ]}}
    +                   },
    +            'f32m': {'topic': 'fedora',
    +                    'version': '32m',
    +                    'modules': ['fedora', 'fedora-secondary'],
    +                    'repos': {'updates': {
    +                        'from': 'f32-modular-updates',
    +                        'ostrees': [],
    +                        'to': [{'arches': ['x86_64', 'aarch64', 'armhfp', 'source'],
    +                                'dest': os.path.join(FEDORADEST, '32', 'Modular')},
    +                               {'arches': ['ppc64le', 's390x'],
    +                                'dest': os.path.join(FEDORAALTDEST, '32', 'Modular')}
    +                              ]},
    +                              'updates-testing': {
    +                        'from': 'f32-modular-updates-testing',
    +                        'ostrees': [],
    +                        'to': [{'arches': ['x86_64', 'aarch64', 'armhfp', 'source'],
    +                                'dest': os.path.join(FEDORADEST, 'testing', '32', 'Modular')},
    +                               {'arches': ['ppc64le', 's390x'],
    +                                'dest': os.path.join(FEDORAALTDEST, 'testing', '32', 'Modular')}
    +                              ]}}
    +                   },
    +            'f31': {'topic': 'fedora',
                         'version': '31',
                         'modules': ['fedora', 'fedora-secondary'],
                         'repos': {'updates': {

    --- a/roles/bodhi2/backend/tasks/main.yml
    +++ b/roles/bodhi2/backend/tasks/main.yml
    @@ -73,7 +73,7 @@
       # bodhi2/backend/files/koji-sync-listener.py
       # This cronjob runs only once a day.  The listener script runs reactively.
       cron: name="owner-sync" minute="15" hour="4" user="root"
    -      job="/usr/local/bin/lock-wrapper owner-sync '/usr/local/bin/owner-sync-pagure f32 f32-container f32-modular f32-flatpak f31 f31-container f31-flatpak f31-modular f30 f30-container f30-flatpak f30-modular epel8 epel8-playground epel8-modular epel7 dist-6E-epel module-package-list modular'"
    +      job="/usr/local/bin/lock-wrapper owner-sync '/usr/local/bin/owner-sync-pagure f33 f33-container f33-modular f33-flatpak f32 f32-container f32-modular f32-flatpak f31 f31-container f31-flatpak f31-modular f30 f30-container f30-flatpak f30-modular epel8 epel8-playground epel8-modular epel7 dist-6E-epel module-package-list modular'"
           cron_file=update-koji-owner
       when: env == "production"
       tags:

    diff --git a/roles/bodhi2/backend/templates/pungi.module.conf.j2 b/roles/bodhi2/backend/templates/pungi.module.conf.j2
    index a594069..266cbf9 100644
    --- a/roles/bodhi2/backend/templates/pungi.module.conf.j2
    +++ b/roles/bodhi2/backend/templates/pungi.module.conf.j2
    @@ -16,6 +16,8 @@ sigkeys = [
     	'cfc659b9',
     [% elif release.version_int == 31 %]
     	'3c3359c4',
    +[% elif release.version_int == 32 %]
    +	'12c944d0',
     [% elif release.version_int == 8 %]
             '2f86d6a1',
     [% endif %]

    diff --git a/roles/bodhi2/backend/templates/pungi.rpm.conf.j2 b/roles/bodhi2/backend/templates/pungi.rpm.conf.j2
    index adfa110..e68f565 100644
    --- a/roles/bodhi2/backend/templates/pungi.rpm.conf.j2
    +++ b/roles/bodhi2/backend/templates/pungi.rpm.conf.j2
    @@ -31,6 +31,8 @@ sigkeys = [
         '3c3359c4',
     [% elif release.version_int == 32 %]
         '12c944d0',
    +[% elif release.version_int == 33 %]
    +    '9570ff31',
     [% elif release.version_int == 6 %]
         '0608b895',
     [% elif release.version_int == 7 %]

    diff --git a/roles/bodhi2/base/templates/production.ini.j2 b/roles/bodhi2/base/templates/production.ini.j2
    index f6bd701..3ae6711 100644
    --- a/roles/bodhi2/base/templates/production.ini.j2
    +++ b/roles/bodhi2/base/templates/production.ini.j2
    @@ -605,6 +605,8 @@ f{{ FedoraRawhideNumber }}c.pre_beta.mandatory_days_in_testing = 0
     # Rawhide gating - Updates in rawhide don't require any days in testing.
     f{{ FedoraRawhideNumber }}.status = pre_beta
     f{{ FedoraRawhideNumber }}.pre_beta.mandatory_days_in_testing = 0
    +f32.status = pre_beta
    +f32.pre_beta.mandatory_days_in_testing = 0
     ##
     ## Buildroot Override
     ##

    diff --git a/roles/bodhi2/backend/templates/koji_sync_listener.toml b/roles/bodhi2/backend/templates/koji_sync_listener.toml
    --- a/roles/bodhi2/backend/templates/koji_sync_listener.toml
    +++ b/roles/bodhi2/backend/templates/koji_sync_listener.toml
    @@ -36,6 +36,10 @@ arguments = {}
    # XXX If you modify this taglist.  Please also modify the other copy in
    # bodhi2/backend/tasks/main.yml
    taglist = [
    +     "f34",
    +     "f34-container",
    +     "f34-modular",
    +     "f34-flatpak",
          "f33",
          "f33-container",
          "f33-modular",


Greenwave
^^^^^^^^^

Greenwave 需要了解新版本。这是在 `greenwave openshift role`_ 中完成的：

::

    diff --git a/roles/openshift-apps/greenwave/templates/fedora.yaml b/roles/openshift-apps/greenwave/templates/fedora.yaml
    index cf0e9fb..5c2a0f3 100644
    --- a/roles/openshift-apps/greenwave/templates/fedora.yaml
    +++ b/roles/openshift-apps/greenwave/templates/fedora.yaml
    @@ -53,6 +53,7 @@ rules:
     --- !Policy
     id: "taskotron_release_critical_tasks_for_testing"
     product_versions:
    +  - fedora-33
       - fedora-32
       - fedora-31
       - fedora-30
    @@ -66,6 +67,7 @@ rules:
     --- !Policy
     id: "taskotron_release_critical_tasks_for_stable"
     product_versions:
    +  - fedora-33
       - fedora-32
       - fedora-31
       - fedora-30

mbs
^^^

添加新的 rawhide 平台。它在infra ansible repo中的 `mbs role`_ 中完成。

::

    diff --git a/roles/mbs/common/files/default-modules.production/platform-f33.yaml b/roles/mbs/common/files/default-modules.production/platform-f33.yaml
    new file mode 100644
    index 0000000..960356c
    --- /dev/null
    +++ b/roles/mbs/common/files/default-modules.production/platform-f33.yaml
    @@ -0,0 +1,28 @@
    +data:
    +  description: Fedora 33 traditional base
    +  license:
    +    module: [MIT]
    +  name: platform
    +  profiles:
    +    buildroot:
    +      rpms: [bash, bzip2, coreutils, cpio, diffutils, fedora-release, findutils, gawk,
    +        glibc-minimal-langpack, grep, gzip, info, make, patch, redhat-rpm-config,
    +        rpm-build, sed, shadow-utils, tar, unzip, util-linux, which, xz]
    +    srpm-buildroot:
    +      rpms: [bash, fedora-release, fedpkg-minimal, glibc-minimal-langpack, gnupg2,
    +        redhat-rpm-config, rpm-build, shadow-utils]
    +  stream: f33
    +  summary: Fedora 33 traditional base
    +  context: 00000000
    +  version: 1
    +  xmd:
    +    mbs:
    +      buildrequires: {}
    +      commit: f33
    +      requires: {}
    +      koji_tag: module-f33-build
    +      mse: TRUE
    +      virtual_streams: [fedora]
    +document: modulemd
    +version: 1
    +

启用分支组合
^^^^^^^^^^^^^^^^^^^^^^^

我们需要启用分支组合。这是在infra ansbile repo 的 `releng role`_ 中完成的。

::

    --- a/roles/releng/files/branched
    +++ b/roles/releng/files/branched
    @@ -1,3 +1,3 @@
     # branched compose
     #MAILTO=releng-cron@lists.fedoraproject.org
    -#15 7 * * * root TMPDIR=`mktemp -d /tmp/branched.XXXXXX` && cd $TMPDIR && git clone https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f31 && /usr/local/bin/lock-wrapper branched-compose "PYTHONMALLOC=debug LANG=en_US.UTF-8 ./nightly.sh" && sudo -u ftpsync /usr/local/bin/update-fullfiletimelist -l /pub/fedora-secondary/update-fullfiletimelist.lock -t /pub fedora fedora-secondary
    +15 7 * * * root TMPDIR=`mktemp -d /tmp/branched.XXXXXX` && cd $TMPDIR && git clone https://pagure.io/pungi-fedora.git && cd pungi-fedora && git checkout f32 && /usr/local/bin/lock-wrapper branched-compose "PYTHONMALLOC=debug LANG=en_US.UTF-8 ./nightly.sh" && sudo -u ftpsync /usr/local/bin/update-fullfiletimelist -l /pub/fedora-secondary/update-fullfiletimelist.lock -t /pub fedora fedora-secondary

Fedora分支
^^^^^^^^^^^^^^^

在infra ansible repo中将 FedoraBranched 变量设置为True。

::

    --- a/vars/all/FedoraBranched.yaml
    +++ b/vars/all/FedoraBranched.yaml
    @@ -1 +1 @@
    -FedoraBranched: False
    +FedoraBranched: True

将 FedoraBranchedBodhi 变量设置为可在 infra ansible repo 中预先启用。

::

    --- a/vars/all/FedoraBranchedBodhi.yaml
    +++ b/vars/all/FedoraBranchedBodhi.yaml
    @@ -1,2 +1,2 @@
    #options are: prebeta, postbeta, current
    -   FedoraBranchedBodhi: current
    +   FedoraBranchedBodhi: preenable

Koji hub
^^^^^^^^

更新koji hub配置以允许新的koji rawhide标签使用侧边标签

::

    --- a/roles/koji_hub/templates/hub.conf.j2
    +++ b/roles/koji_hub/templates/hub.conf.j2
    @@ +1 @@
    +   tag f34-build :: allow
    tag f33-build :: allow
    tag f32-build :: allow

Robosignatory
^^^^^^^^^^^^^

Robosignatory 有两个部分：

1. 禁用branched签名，这样我们就可以冻结branched，直到我们得到一个compose
2. 添加新版本

两者都可以在infra ansible repo中担任 `robosignatory role`_

::

    --- a/roles/robosignatory/templates/robosignatory.toml.j2
    +++ b/roles/robosignatory/templates/robosignatory.toml.j2
    @@ -218,23 +218,23 @@ handlers = ["console"]

                 # Gated rawhide and branched

    -            [[consumer_config.koji_instances.primary.tags]]
    -            from = "f32-signing-pending"
    -            to = "f32-updates-testing-pending"
    -            key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    -            keyid = "{{ (env == 'production')|ternary('12c944d0', 'd300e724') }}"
    -
    -            [consumer_config.koji_instances.primary.tags.sidetags]
    -            pattern = 'f32-build-side-<seq_id>'
    -            from = '<sidetag>-signing-pending'
    -            to = '<sidetag>-testing-pending'
    -            trusted_taggers = ['bodhi']
    -
    -            [[consumer_config.koji_instances.primary.tags]]
    -            from = "f32-pending"
    -            to = "f32"
    -            key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    -            keyid = "{{ (env == 'production')|ternary('12c944d0', 'd300e724') }}"
    +#            [[consumer_config.koji_instances.primary.tags]]
    +#            from = "f32-signing-pending"
    +#            to = "f32-updates-testing-pending"
    +#            key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    +#            keyid = "{{ (env == 'production')|ternary('12c944d0', 'd300e724') }}"
    +
    +#            [consumer_config.koji_instances.primary.tags.sidetags]
    +#            pattern = 'f32-build-side-<seq_id>'
    +#            from = '<sidetag>-signing-pending'
    +#            to = '<sidetag>-testing-pending'
    +#            trusted_taggers = ['bodhi']
    +
    +#            [[consumer_config.koji_instances.primary.tags]]
    +#            from = "f32-pending"
    +#            to = "f32"
    +#            key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    +#            keyid = "{{ (env == 'production')|ternary('12c944d0', 'd300e724') }}"

                 [[consumer_config.koji_instances.primary.tags]]
                 from = "f32-modular-pending"

    --- a/roles/robosignatory/templates/robosignatory.toml.j2
    +++ b/roles/robosignatory/templates/robosignatory.toml.j2
    @@ -216,8 +216,46 @@ handlers = ["console"]
                 key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
                 keyid = "{{ (env == 'production')|ternary('12c944d0', 'd300e724') }}"

    +            [[consumer_config.koji_instances.primary.tags]]
    +            from = "f33-coreos-signing-pending"
    +            to = "coreos-pool"
    +            key = "{{ (env == 'production')|ternary('fedora-33', 'testkey') }}"
    +            keyid = "{{ (env == 'production')|ternary('9570ff31', 'd300e724') }}"
    +
                 # Gated rawhide and branched

    +            [[consumer_config.koji_instances.primary.tags]]
    +            from = "f33-signing-pending"
    +            to = "f33-updates-testing-pending"
    +            key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    +            keyid = "{{ (env == 'production')|ternary('12c944d0', 'd300e724') }}"
    +
    +            [consumer_config.koji_instances.primary.tags.sidetags]
    +            pattern = 'f33-build-side-<seq_id>'
    +            from = '<sidetag>-signing-pending'
    +            to = '<sidetag>-testing-pending'
    +            trusted_taggers = ['bodhi']
    +
    +            [[consumer_config.koji_instances.primary.tags]]
    +            from = "f33-pending"
    +            to = "f33"
    +            key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    +            keyid = "{{ (env == 'production')|ternary('12c944d0', 'd300e724') }}"
    +
    +            [[consumer_config.koji_instances.primary.tags]]
    +            from = "f33-modular-pending"
    +            to = "f33-modular"
    +            key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    +            keyid = "{{ (env == 'production')|ternary('12c944d0', 'd300e724') }}"
    +            type = "modular"
    +
    +            [[consumer_config.koji_instances.primary.tags]]
    +            from = "f33-modular-updates-candidate"
    +            to = "f33-modular"
    +            key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    +            keyid = "{{ (env == 'production')|ternary('12c944d0', 'd300e724') }}"
    +            type = "modular"
    +
     #            [[consumer_config.koji_instances.primary.tags]]
     #            from = "f32-signing-pending"
     #            to = "f32-updates-testing-pending"
    @@ -469,15 +507,43 @@ handlers = ["console"]
             directory = "/mnt/fedora_koji/koji/compose/ostree/repo/"
             key = "{{ (env == 'production')|ternary('fedora-31', 'testkey') }}"

    -        [consumer_config.ostree_refs."fedora/rawhide/aarch64/silverblue"]
    +        [consumer_config.ostree_refs."fedora/32/x86_64/silverblue"]
             directory = "/mnt/fedora_koji/koji/compose/ostree/repo/"
             key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    -        [consumer_config.ostree_refs."fedora/rawhide/ppc64le/silverblue"]
    +        [consumer_config.ostree_refs."fedora/32/aarch64/silverblue"]
             directory = "/mnt/fedora_koji/koji/compose/ostree/repo/"
             key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    -        [consumer_config.ostree_refs."fedora/rawhide/x86_64/silverblue"]
    +        [consumer_config.ostree_refs."fedora/32/ppc64le/silverblue"]
    +        directory = "/mnt/fedora_koji/koji/compose/ostree/repo/"
    +        key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    +        [consumer_config.ostree_refs."fedora/32/x86_64/updates/silverblue"]
    +        directory = "/mnt/fedora_koji/koji/compose/ostree/repo/"
    +        key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    +        [consumer_config.ostree_refs."fedora/32/x86_64/testing/silverblue"]
    +        directory = "/mnt/fedora_koji/koji/compose/ostree/repo/"
    +        key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    +        [consumer_config.ostree_refs."fedora/32/aarch64/updates/silverblue"]
    +        directory = "/mnt/fedora_koji/koji/compose/ostree/repo/"
    +        key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    +        [consumer_config.ostree_refs."fedora/32/aarch64/testing/silverblue"]
             directory = "/mnt/fedora_koji/koji/compose/ostree/repo/"
             key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    +        [consumer_config.ostree_refs."fedora/32/ppc64le/updates/silverblue"]
    +        directory = "/mnt/fedora_koji/koji/compose/ostree/repo/"
    +        key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    +        [consumer_config.ostree_refs."fedora/32/ppc64le/testing/silverblue"]
    +        directory = "/mnt/fedora_koji/koji/compose/ostree/repo/"
    +        key = "{{ (env == 'production')|ternary('fedora-32', 'testkey') }}"
    +
    +        [consumer_config.ostree_refs."fedora/rawhide/aarch64/silverblue"]
    +        directory = "/mnt/fedora_koji/koji/compose/ostree/repo/"
    +        key = "{{ (env == 'production')|ternary('fedora-33', 'testkey') }}"
    +        [consumer_config.ostree_refs."fedora/rawhide/ppc64le/silverblue"]
    +        directory = "/mnt/fedora_koji/koji/compose/ostree/repo/"
    +        key = "{{ (env == 'production')|ternary('fedora-33', 'testkey') }}"
    +        [consumer_config.ostree_refs."fedora/rawhide/x86_64/silverblue"]
    +        directory = "/mnt/fedora_koji/koji/compose/ostree/repo/"
    +        key = "{{ (env == 'production')|ternary('fedora-33', 'testkey') }}"


         [consumer_config.coreos]

推送更改
^^^^^^^^^^^^^^^^

编辑完文件后，通过相应的ansible playbook提交、推送和应用它们：

::

    sudo rbac-playbook groups/koji-hub.yml
    sudo rbac-playbook groups/releng-compose.yml
    sudo rbac-playbook groups/bodhi-backend.yml
    sudo rbac-playbook openshift-apps/greenwave.yml
    sudo -i ansible-playbook /srv/web/infra/ansible/playbooks/groups/proxies.yml -t pkgdb2
    sudo rbac-playbook groups/mbs.yml -t mbs

请fedora infra的人来执行robosignatory playbook.


Koji
----
Koji构建系统需要进行一些标签/目标工作，以处理来自新分支的构建并更新从rawhide进行构建的位置。

在 `pagure releng`_ 仓库中运行 `make-koji-release-tags`_ 脚本


Fedora 版本
--------------
``fedora-release`` 包需要在Rawhide和Branched中进行更新。

在 **rawhide** 分支中更改 ``fedora-release.spec``：

1. 增加 ``%define dist_version``::

    -%define dist_version 35
    +%define dist_version 36

2. 增加 ``Version:`` 并重置 ``Release:``::

    -Version:        35
    -Release:        0.3%{?eln:.eln%{eln}}
    +Version:        36
    +Release:        0.1%{?eln:.eln%{eln}}

3. 添加 ``%changelog`` 条目::

     %changelog
    +* Tue Feb 23 2021 Mohan Boddu <mboddu@bhujji.com> - 36-0.1
    +- Setup for rawhide being F36

在 **branched** 分支中更改 ``fedora-release.spec`` ：

1. 调整 ``release_name`` 并取消 ``is_rawhide``::

    -%define release_name Rawhide
    -%define is_rawhide 1
    +%define release_name Thirty Five
    +%define is_rawhide 0

2. 验证 ``dist_version`` 和 ``Version:`` 的正确编号::

    %define dist_version 35
    Version:        35

3. 改变 ``Release:``::

    -Release:        0.3%{?eln:.eln%{eln}}
    +Release:        0.4%{?eln:.eln%{eln}}

3. 添加 ``%changelog`` 条目::

     %changelog
    +* Tue Feb 23 2021 Mohan Boddu <mboddu@bhujji.com> - 35-0.4
    +- Branching F35 from rawhide


Fedora Repos
------------

``fedora-repos`` 包需要在Rawhide、Branched以及所有稳定发布的分支中进行更新（以便接收新的GPG密钥和更新的符号链接）。

更改 **rawhide** 分支 (主要在 ``fedora-repos.spec`` 中):

1. 生成并添加一个 *Rawhide+1* GPG 密钥文件，然后将其添加到spec文件中::

    Source57:       RPM-GPG-KEY-fedora-37-primary

2. 更新 ``archmap`` 文件并定义 *Rawhide+1* 的体系结构::

    +fedora-37-primary: x86_64 armhfp aarch64 ppc64le s390x

3. 增加 ``%global rawhide_release``::

    -%global rawhide_release 35
    +%global rawhide_release 36

4. 改变 ``Version:`` 并重置 ``Release:``::

    -Version:        35
    -Release:        0.2%{?eln:.eln%{eln}}
    +Version:        36
    +Release:        0.1%{?eln:.eln%{eln}}

5. 添加 ``%changelog`` 条目::

     %changelog
    +* Tue Feb 23 2021 Tomas Hrcka <thrcka@redhat.com> - 36-0.1
    +- Setup for rawhide being F36

更改 **branched** 分支 (主要在 ``fedora-repos.spec`` 中):

1. 从 *rawhide* 分支复制 *Rawhide+1* GPG 密钥文件，然后将其添加到spec文件中::

    Source57:       RPM-GPG-KEY-fedora-37-primary

2. 从 *rawhide* 分支复制 ``archmap`` 文件。
3. 更新 ``%global rawhide_release``::

    -%global rawhide_release 35
    +%global rawhide_release 36

4. 启用 ``updates_testing_enabled``::

    -%global updates_testing_enabled 0
    +%global updates_testing_enabled 1

5. 改变 ``Release:``::

    -Release:        0.2%{?eln:.eln%{eln}}
    +Release:        0.3%{?eln:.eln%{eln}}

6. 添加 ``%changelog`` 条目::

     %changelog
    +* Tue Feb 23 2021 Tomas Hrcka <thrcka@redhat.com> - 35-0.3
    +- Update Rawhide definition, enable updates-testing for Branched

.. note::
    在 **启用Rawhide门控之前**，先构建适用于Branched版本的 ``fedora-release`` 和 ``fedora-repos`` 软件包。

更改 **stable** 分支 (主要在 ``fedora-repos.spec`` 中):

1. 从*rawhide* 分支复制 *Rawhide+1* GPG 密钥文件，然后将其添加到spec文件中::

    Source57:       RPM-GPG-KEY-fedora-37-primary

2. 从 *rawhide* 分支复制 ``archmap`` 文件。
3. 更新 ``%global rawhide_release``::

    -%global rawhide_release 35
    +%global rawhide_release 36

4. 改变 ``Release:``::

    -Release:        0.2%{?eln:.eln%{eln}}
    +Release:        0.3%{?eln:.eln%{eln}}

5. 添加 ``%changelog`` 条目::

     %changelog
    +* Tue Feb 23 2021 Tomas Hrcka <thrcka@redhat.com> - 34-0.3
    +- Update Rawhide definition


Bodhi
-----

链接空仓库
^^^^^^^^^^^^^^^^^^^

我们需要链接空仓库，以便new-updates-sync不会抱怨缺少仓库。以下命令应在 **bodhi-backend01.phx2.fedoraproject.org** 上运行

::

    $ sudo ln -s /mnt/koji/compose/updates/empty-repo/ /mnt/koji/compose/updates/f32-updates
    $ sudo ln -s /mnt/koji/compose/updates/empty-repo/ /mnt/koji/compose/updates/f32-updates-testing
    $ sudo ln -s /mnt/koji/compose/updates/empty-repo/ /mnt/koji/compose/updates/f32-modular-updates
    $ sudo ln -s /mnt/koji/compose/updates/empty-repo/ /mnt/koji/compose/updates/f32-modular-updates-testing

创建空仓库
^^^^^^^^^^^^^^^^^^^^

要在主镜像上创建空仓库，请从 `pagure releng`_ 仓库运行 `create_emtpy_repos.sh`_ 。这应该在 **bodhi-backend01.phx2.fedoraproject.org** 上运行

::

    $ sudo -u ftpsync sh scripts/branching/create_empty_repos.sh 31

.. note::
    请验证创建在 /pub/fedora/linux/development/<fedora_release_number>
    和 /pub/fedora-secondary/development/<fedora_release_number> 下的仓库权限，他们应该归属于 *ftpsync:ftpsync*

创建 rawhide 版本
^^^^^^^^^^^^^^^^^^^^^^^^

在bodhi中创建rawhide版本，您需要运行

::

    $ bodhi releases create --name "F36" --long-name "Fedora 36" --id-prefix FEDORA --version 36 --branch f36 --dist-tag f36 --stable-tag f36 --testing-tag f36-updates-testing --candidate-tag f36-updates-candidate --pending-stable-tag f36-updates-pending --pending-testing-tag f36-updates-testing-pending --pending-signing-tag f36-signing-pending --state pending --override-tag f36-override --create-automatic-updates --not-composed-by-bodhi

要在bodhi中创建rawhide的容器版本，您需要运行

::

    $ bodhi releases create --name "F36C" --long-name "Fedora 36 Containers" --id-prefix FEDORA-CONTAINER --version 36 --branch f36 --dist-tag f36-container --stable-tag f36-container-updates --testing-tag f36-container-updates-testing --candidate-tag f36-container-updates-candidate --pending-stable-tag f36-container-updates-pending --pending-testing-tag f36-container-updates-testing-pending --state pending --override-tag f36-container-override

要为bodhi的branched分支创建flatpak版本，您需要运行

::

    $ bodhi releases create --name "F35F" --long-name "Fedora 35 Flatpaks" --id-prefix FEDORA-FLATPAK --version 35 --branch f35 --dist-tag f35-flatpak --stable-tag f35-flatpak-updates --testing-tag f35-flatpak-updates-testing --candidate-tag f35-flatpak-updates-candidate --pending-stable-tag f35-flatpak-updates-pending --pending-testing-tag f35-flatpak-updates-testing-pending --state pending --override-tag f35-flatpak-override

您需要运行 ``bodhi openshift`` 行动手册，以便UI了解新版本。然后，您需要重新启动 **bodhi-backend01.phx2.fedoraproject.org** 上的 **fm-consumer@config.service** 和 **bodhi-celery.service**。


::

    $ sudo rbac-playbook openshift-apps/bodhi.yml
    $ sudo systemctl restart fm-consumer@config.service bodhi-celery.service


.. note::
    在 **启用rawhide门控之后**，为rawhide构建fedora-release，fedora-repos软件包

更新 rawhide koji 仓库
^^^^^^^^^^^^^^^^^^^^^^^^

我们需要将 *rawhide* buildroot 仓库指向新创建的 rawhide buildroot。这样kojira就不会像fxx-build (新的 rawhide buildroot) 那样频繁地为 *rawhide* 目标创建新的仓库。

从任意组合框运行以下命令

::
    $ cd /mnt/koji/repos/rawhide; rm -f latest; ln -s ../f34-build/latest ./latest

更新 block_retired.py 脚本
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

releng仓库中的 `block_retired.py`_ 脚本应使用rawhide版本进行更新，还应将branched版本添加到脚本中。

请以这个 `block_retired.py commit`_ 为例。

更新 MirrorManager
^^^^^^^^^^^^^^^^^^^^^^

我们需要更新mirrormanager，以便它将rawhide指向新的rawhide版本。

请按照 `fedora infra ticket`_ 中的说明更新mirrormanager的数据库。

在分支版本上启用自动签名
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

一旦branched compose被组合，我们需要重新启用Robosignatory的branched版本

ELN相关工作
^^^^^^^^^^^^^^^^

将新的rawhide密钥添加到eln pungi配置中。例如看看这个 `pungi eln config commit`_

将 DistroBuildSync 的触发通知更改为新的Rawhide版本。例如，看看这个 `commit <https://gitlab.com/redhat/centos-stream/ci-cd/distrosync/distrobuildsync-config/-/commit/1497d9aea42cf00af646b4a0f9f9ed1a7f0a477f>`_.

在 Koschei 建新rawhide分支
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

在 `koschei <https://docs.fedoraproject.org/en-US/infra/sysadmin_guide/koschei/#_branching_a_new_fedora_release>`_ 建新的fedora rawhide分支。


Fedora 容器基础镜像
---------------------------

为了通过 `Fedora Layered
Image Build System`_ 启用容器基础镜像的构建，我们需要为Rawhide导入一个新的镜像，并为新的 ``fedora:rawhide`` 和 ``fedora:${RAWHIDE}`` 标签导入一个新的镜像。

您可以在 `此处
<https://koji.fedoraproject.org/koji/packageinfo?packageID=21546>`_ 检查最新成功的Rawhide基础镜像的组合镜像：

在 ``compose-x86-01.phx2`` 运行时：

::

    # Update this to be the correct URL for your image
    $ BASEIMAGE_URL="https://kojipkgs.fedoraproject.org//packages/Fedora-Docker-Base/Rawhide/20170310.n.0/images/Fedora-Docker-Base-Rawhide-20170310.n.0.x86_64.tar.xz"

    # Update this to whatever version number Rawhide now points to
    $ RAWHIDE="27"

    # Load the latest, find it's image name
    $ sudo docker load < <(curl -s "${BASEIMAGE_URL}")
    $ sudo docker images | grep base-rawhide
    fedora-docker-base-rawhide-20170310.n.0.x86_64      latest      ffd832a990ca        5 hours ago     201.8 MB

    # Tag everything
    $ sudo docker tag fedora-docker-base-rawhide-20170310.n.0.x86_64 candidate-registry.fedoraproject.org/fedora:rawhide
    $ sudo docker tag fedora-docker-base-rawhide-20170310.n.0.x86_64 candidate-registry.fedoraproject.org/fedora:${RAWHIDE}
    $ sudo docker tag fedora-docker-base-rawhide-20170310.n.0.x86_64 registry.fedoraproject.org/fedora:rawhide
    $ sudo docker tag fedora-docker-base-rawhide-20170310.n.0.x86_64 registry.fedoraproject.org/fedora:${RAWHIDE

    # Push the images
    $ sudo docker push candidate-registry.fedoraproject.org/fedora:rawhide
    $ sudo docker push candidate-registry.fedoraproject.org/fedora:${RAWHIDE}
    $ sudo docker push registry.fedoraproject.org/fedora:rawhide
    $ sudo docker push registry.fedoraproject.org/fedora:${RAWHIDE}

    # Clean up after ourselves
    $ sudo docker rmi fedora-docker-base-rawhide-20170310.n.0.x86_64
    Untagged: fedora-docker-base-rawhide-20170310.n.0.x86_64:latest
    $ for i in $(sudo docker images -q -f 'dangling=true'); do sudo docker rmi $i; done

更新同步脚本
^^^^^^^^^^^^^^^^^^

更新 releng 仓库中的 `脚本
<https://pagure.io/releng/blob/main/f/scripts/sync-latest-container-base-image.sh#_38>`_.

并设置 current_rawhide 变量。

运行之前请考虑
=======================

.. note::
    FIXME: Need some love here



.. _pkgdb-proxy role:
    https://pagure.io/fedora-infra/ansible/blob/main/f/roles/pkgdb-proxy
.. _packages3 role:
    https://pagure.io/fedora-infra/ansible/blob/main/f/roles/packages3
.. _bodhi2 role:
    https://pagure.io/fedora-infra/ansible/blob/main/f/roles/bodhi2
.. _greenwave openshift role:
    https://pagure.io/fedora-infra/ansible/blob/main/f/roles/openshift-apps/greenwave
.. _mbs role:
    https://pagure.io/fedora-infra/ansible/blob/main/f/roles/mbs
.. _releng role:
    https://pagure.io/fedora-infra/ansible/blob/main/f/roles/releng
.. _robosignatory role:
    https://pagure.io/fedora-infra/ansible/blob/main/f/roles/robosignatory
.. _make-koji-release-tags:
    https://pagure.io/releng/blob/main/f/scripts/branching/make-koji-release-tags
.. _pagure releng:
    https://pagure.io/releng
.. _create_emtpy_repos.sh:
    https://pagure.io/releng/blob/main/f/scripts/branching/create_empty_repos.sh
.. _Fedora Layered Image Build System:
    https://docs.pagure.org/releng/layered_image_build_service.html
.. _fedscm-admin commit:
    https://pagure.io/fedscm-admin/c/7862d58b5982803dbe4c47e0262c6ce78bc903db?branch=main
.. _block_retired.py:
    https://pagure.io/releng/blob/main/f/scripts/block_retired.py
.. _block_retired.py commit:
    https://pagure.io/releng/c/9eb97f491f7a767ab8b90498adfa3b34ee235247?branch=main
.. _fedora infra ticket:
    https://pagure.io/fedora-infrastructure/issue/9239#comment-671446
.. _pungi eln config commit:
    https://pagure.io/pungi-fedora/c/e993441164ee83374df7f463777f2bf1d456fd6d?branch=eln
