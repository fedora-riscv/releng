.. SPDX-License-Identifier:    CC-BY-SA-3.0


==========
组成Fedora
==========

说明
====
所有组合都是由保存在 `pungi-fedora repository`_ 仓库中的配置文件定义的。

组合分为两类。它们可能是按需创建的候选版本，也可能是设置为每天夜间在预定时间运行的组合。

=============== ===================== =======================
Compose名称     配置文件              Compose脚本
=============== ===================== =======================
Docker          fedora-docker.conf    docker-nightly.sh
Cloud           fedora-cloud.conf     cloud-nightly.sh
Modular         fedora-modular.conf   modular-nightly.sh
Nightly         fedora.conf           nightly.sh
=============== ===================== =======================

当质量工程师（QE）请求一个候选版本（RC）时，他们通过在pagure上打开releng仓库中的issue来完成。候选版本的组成当前未实现自动化。

=============== ===================== =======================
Compose名称     配置文件              Compose脚本
=============== ===================== =======================
Beta            fedora-beta.conf      release-candidate.sh
GA              fedora-final.conf     release-candidate.sh
=============== ===================== =======================

操作
====
以下程序仅适用于候选版本。它们不适用于预定的夜间组合。

审查compose标签
---------------
#. 在当前compose标签中列出所有预先存在的构建

   ::

        $ koji list-tagged f[release_version]-compose

#. 验证compose标签中预先存在的构建

   来自上一个组合的已标记的构建应该都出现在来自上一步的输出中。请查阅请求票证，了解此输出中预期的构建列表。

   .. note::
      Beta或GA compose的第一次运行应该在compose标签下不含任何构建。在Beta和RC compose之间移动时，从compose标签中清除预先存在的构建非常重要。请验证这些构建是否已删除。

      ::

           $ koji list-tagged f[release_version]-compose
           $ koji untag-build --all f[release_version]-compose [build1 build2 ...]

   .. note::
      将包添加到f[release_version]-compose标签中的顺序很重要。如果构建没有被错误地标记，那么应该特别注意正确地添加它们。


#. 将QE指定的构建添加到当前的compose标签中

   ::

        $ koji tag-build f[release_version]-compose [build1 build2 ...]

   .. note::
       只要用户在koji工具中具有适当的权限，这些步骤就可以在本地机器上完成。

Compose之前的包签名
-------------------
#. 检查未签名的包

   ::

        $ koji list-tagged f[release_version]-signing-pending

   .. note::
      如果有未签名的构建，请等待自动队列将其提取并签名。如果包签名耗时超过30分钟，请联系Fedora基础设施团队的成员。


运行Compoese
------------
#. 更新pungi-fodora配置文件Composes使用配置文件来构造compose。每个compose都使用自己的配置。
   ``global_release`` 变量应该从1.1开始，第二个数字应该在每次创建新的compose时递增。

   * Beta - ``fedora-beta.conf``
   * RC - ``fedora-final.conf``

#. 登录到compose后端

   ::

        $ ssh compose-x86-01.phx2.fedoraproject.org

#. 打开屏幕会话

   ::

        $ screen

#. 获取当前compose的pungi-fedora分支

   任何用户帐户第一次执行compose时，必须克隆pungi-fedora git仓库。调用pungi的compose候选脚本应该从 ``compose-x86-01.iad2.fedoraproject.org`` 开始运行。

   ::

        $ git clone ssh://git@pagure.io/pungi-fedora.git

   进入 pungi-fedora 目录。

   ::

        $ cd pungi-fedora

   如果不需要上述克隆步骤，则从pagure中checkout完整更新现有仓库。

   ::

        $ git fetch origin
        $ git checkout f[release_version]
        $ git pull origin f[release_version]

#. 运行compose

   ::

        $ sudo ./release-candidate.sh [Beta|RC]-#.#

   编号方案从1.1开始，第二个数字在每次compose后递增。

   .. note::
      Pungi要求数字的格式为#.#作为参数。正因为如此，compose总是从数字1开始，第二个数字随着每次compose而递增。

   .. note::
       如果compose失败，并出现找不到目录的错误，则使用 ``mkdir /mnt/koji/compose/[release_version]`` 创建compose目录。

同步Compose
-------------------

我们将compose同步到 ``/pub/alt/stage`` ，以便QA和更大的Fedora社区能够更快地访问新内容。

#. 登录到compose后端

   ::

        $ ssh compose-x86-01.iad2.fedoraproject.org

#. 打开一个屏幕会话

   ::

        $ screen

#. 检查compose的状态

   ::

        $  cat /mnt/koji/compose/[release_version]/[compose_id]/STATUS

   如果输出是 ``DOOMED``，请不要继续执行任何进一步的步骤。

#. 创建副本的目标目录
   ::

        $ sudo -u ftpsync mkdir -m 750 -p /pub/alt/stage/[release_version]_[release_label]-[#.#]

#. 找到将作为复制源的compose目录
   ::

        $ ls /mnt/koji/compose/[release_version]/[compose_id]

   .. note::
      如果下一个compose已经在运行，请注意执行同步。一定要获取正确的目录。

      如果有疑问，请检查/mnt/koji/compose/[release_version]/[compose_id]/STATUS以确保完成。

#. 运行同步的一行程序

   将完成的compose同步到公共域目前是一个单行shell脚本。请密切注意以下示例中需要替换的内容。

   ::

        $ sudo -u ftpsync sh -c 'for dir in Everything Cloud Container Kinoite Labs Modular Server Silverblue Spins Workstation metadata; do rsync -avhH /mnt/koji/compose/31/Fedora-31-20190911.0/compose/$dir/ /pub/alt/stage/31_Beta-1.1/$dir/ --link-dest=/pub/fedora/linux/development/31/Everything/ --link-dest=/pub/alt/stage/31_Beta-1.1/Everything/; done'

   .. note::
      如果多个compose像1.2、1.3那样运行，请在上面添加多个–link-dest参数和多个composes

#. 设置同步compose的权限
   ::

        $ sudo -u ftpsync chmod 755 /pub/alt/stage/[release_version]_[release_label]-[#.#]

#. 更新releng pagure仓库中的issue 

   一旦compose和同步完成，pagure中的issue就应该更新并关闭。

   .. admonition:: 标准票证Verbage

      Compose已经完成，可以从 https://kojipkgs.fedoraproject.org/compose/26/Fedora-26-20170328.0/compose/ 开始使用，它已经同步到 http://dl.fedoraproject.org/pub/alt/stage/26_Alpha-1.4/ ，rpms都已硬链接到 /pub/fedora/linux/development/26/

验证
^^^^

验证撰写是否已完成的方法是检查 ``/mnt/koji/compose/[release_version]/[compose_dir]/STATUS``，除DOOMED之外的任何状态都正常。

预发布工作
================

将更新推送到stable
-------------------------

当周四Go/No-Go会议后签署版本时，将freeze和blocker推送至stable更新

通常情况下，QA会请求stable更新。如果更新不可用，您可以通过以下方式请求更新

::

   $ bodhi updates request <updateid> stable

一旦请求stable更新，请按照 `bodhi push to stable sop`_ 将其推送至stable

koji标签更改
------------

一旦更新被推送到stable，我们需要克隆koji标签进行beta发布，或者为最终版本锁定koji标签。

对于测试版
^^^^^^^^^^^^^^^^

::

   $ koji clone-tag --all --latest-only f31 f31-Beta
   $ koji clone-tag --all --latest-only f31-modular f31-Beta-modular

对于最终版
^^^^^^^^^^^^^^^^^

::

   $ koji edit-tag --lock f31
   $ koji edit-tag --lock f31-modular

Bodhi变更
-------------

将bodhi版本设置为 ``current``

::

   $ bodhi releases edit --name F31 --state current

最终版本的更改
=========================

一旦最终版本完成，我们需要执行与Beta版本不同的更改。

最后一次分支compose
---------------------

手动运行一个分支compose，以便GOLD内容与夜间compose相同。这也有助于将silverblue参考更新为GOLD内容的参考。

更新silverblue参考
----------------------

请根据 `bodhi-backend01.phx2.fedoraproject.org` 上的以下命令更新参考文件

从 `/mnt/koji/compose/ostree/repo` 和 `/mnt/koji/ostree/repo/` 运行以下命令

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

仅从 `/mnt/koji/ostree/repo/` 运行以下命令

::

   $ sudo ostree summary -u

.. note::
   在将更新推送到fxx-updates之前，请运行最后一次分支compose，以便分支和rc compose都具有相同的内容。一旦分支compose完成，然后如上所述更新silverblue参考。如果顺序改变了，就会把参考文件搞砸。


禁用分支Compose
------------------------

现在我们有了最后的GOLD compose，我们不再需要夜间分支compose了。这在infra ansible repo中的 `releng role`_ 中被禁用，然后运行playbook。

::

   $ sudo rbac-playbook groups/releng-compose.yml


解除RelEng冻结
------------------

解除RelEng冻结，以便将更新推至stable。这是通过编辑infra ansible repo中的 `RelEngFrozen variable`_ ，然后运行bodhi playbook来完成的。

::

   $ sudo rbac-playbook groups/bodhi-backend.yml

其他更改
-------------

这些更改包括启用夜间容器和云组合、infra ansible repo中的其他变量更改、bodhi pungi配置更改、更新同步更改等。

在进行以下更改后运行相应的playbook

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

Bodhi配置
------------

测试版之后
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

最终版之后
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


镜像
---------

运行 `bodhi-backend01.phx2.fedoraproject.org` pagure中 `releng repo`_ 的 `stage-release.sh` 脚本，这将对校验和进行签名，并将内容放在镜像上。

对于测试版
^^^^^^^^^^^^^^^^

::

   $ sh scripts/stage-release.sh 32_Beta Fedora-32-20200312.0 32_Beta-1.2 fedora-32 1

对于最终版
^^^^^^^^^^^^^^^^^^

::

   $ sh scripts/stage-release.sh 32 Fedora-32-20200415.0 32_RC-1.1 fedora-32 0

.. note::
   确保获取目录大小使用发送电子邮件到 `mirror-admin@lists.fedoraproject.org` 列表的编号。


将已签名的校验和同步到stage
----------------------------------

我们需要通过运行以下命令将已签名的校验和同步到 /pub/alt/stage/

::

   $ for dir in Everything Cloud Container Labs Server Spins Workstation Silverblue Kinoite metadata; do sudo -u ftpsync rsync -avhH /mnt/koji/compose/37/Fedora-37-20221105.0/compose/$dir/ /pub/alt/stage/37_RC-1.7/$dir/ --link-dest=/pub/fedora/linux/releases/37/Everything/ --link-dest=/pub/alt/stage/37_RC-1.2/Everything/ --link-dest=/pub/alt/stage/37_RC-1.3/Everything --link-dest=/pub/alt/stage/37_RC-1.4/Everything --link-dest=/pub/alt/stage/37_RC-1.5/Everything --link-dest=/pub/alt/stage/37_RC-1.6/Everything --link-dest=/pub/alt/stage/37_RC-1.7/Everything; done

使用mirrormanager将开发移至发布文件夹
=====================================================

发布两周后，将bits从开发转移到发布目录

#. ssh到mm-backend01.iad2.fedoraproject.org
      ::
         $ ssh mm-backend01.iad2.fedoraproject.org

#. 获取root
      ::
         $ sudo su

#. 运行mm2_move-devel-to-release
      ::
         $ mm2_move-devel-to-release --version=35 --category='Fedora Linux'


运行之前请考虑
=======================
合成和文件同步应在远程计算机上的屏幕会话中运行。这需要运营商能够承受网络连接问题。

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

