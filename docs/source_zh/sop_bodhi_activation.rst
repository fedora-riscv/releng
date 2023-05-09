.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
Bodhi 激活点
===========================

说明
===========
.. Put a description of the task here.

Bodhi必须在14:00 UTC的 `Mass Branching`_ 两周后激活。

操作
======
.. Describe the action and provide examples

koji 变更
^^^^^^^^^^^^^^^^^^^

对koji标签作出以下更改

::

  $ koji remove-tag-inheritance f33-updates-candidate f33
  $ koji remove-tag-inheritance f33-updates-testing f33
  $ koji remove-tag-inheritance f33-updates-pending f33
  $ koji remove-tag-inheritance f33-override f33
  $ koji add-tag-inheritance f33-updates-candidate f33-updates
  $ koji add-tag-inheritance f33-updates-testing f33-updates
  $ koji add-tag-inheritance f33-updates-pending f33-updates
  $ koji add-tag-inheritance f33-override f33-updates
  $ koji edit-tag --perm=admin f33

更新 bodhi rpm 版本
^^^^^^^^^^^^^^^^^^^^^^^^

将 bodhi rpm 设置为release而不是自动创建更新，并且Bodhi知道如何组合更新。

::

  $ bodhi releases edit --name "F33" --stable-tag f33-updates --testing-repository updates-testing --package-manager dnf --no-create-automatic-updates --composed-by-bodhi

添加 modular 版本
^^^^^^^^^^^^^^^^^^^^^^^

在您自己的工作站上运行以下命令以添加 modular 版本

::

  $ bodhi releases create --name F33M --long-name "Fedora 33 Modular" --id-prefix FEDORA-MODULAR --version 33 --branch f33m --dist-tag f33-modular --stable-tag f33-modular-updates --testing-tag f33-modular-updates-testing --candidate-tag f33-modular-updates-candidate --pending-stable-tag f33-modular-updates-pending --pending-testing-tag f33-modular-updates-testing-pending --pending-signing-tag f33-modular-signing-pending --override-tag f33-modular-override --state pending --user mohanboddu

.. warning:: 由于Bodhi中的一个 `bug <https://github.com/fedora-infra/bodhi/issues/2177>`_ ，在使用 ``bodhi releases create`` 或
    ``bodhi releases edit`` 的任何时候都必须重新启动Bodhi进程

.. note:: 如果容器和flatpak版本尚未添加到bodhi中，请添加它们

Ansible 变更
===============

更新变量
^^^^^^^^^^^

更新infra ansible中的 *FedoraBranchedBodhi* 和 *RelEngFrozen* 变量

::

  diff --git a/vars/all/FedoraBranchedBodhi.yaml b/vars/all/FedoraBranchedBodhi.yaml
  index aba8be2..606eb2e 100644
  --- a/vars/all/FedoraBranchedBodhi.yaml
  +++ b/vars/all/FedoraBranchedBodhi.yaml
  @@ -3,4 +3,4 @@
  # prebeta: After bodhi enablement/beta freeze and before beta release
  # postbeta: After beta release and before final release
  # current: After final release
  -FedoraBranchedBodhi: preenable
  +FedoraBranchedBodhi: prebeta
  diff --git a/vars/all/RelEngFrozen.yaml b/vars/all/RelEngFrozen.yaml
  index 5836689..87d85f3 100644
  --- a/vars/all/RelEngFrozen.yaml
  +++ b/vars/all/RelEngFrozen.yaml
  @@ -1 +1 @@
  -RelEngFrozen: False
  +RelEngFrozen: True

更新 Greenwave 策略
^^^^^^^^^^^^^^^^^^^^^^^

现在编辑 Greenwave 策略，通过在Infrastructure Ansible存储库中编辑
``roles/openshift-apps/greenwave/templates/configmap.yml`` 来为新版本配置策略。

:: 

  diff --git a/roles/openshift-apps/greenwave/templates/fedora.yaml b/roles/openshift-apps/greenwave/templates/fedora.yaml
  index 7a76f61..d15e154 100644
  --- a/roles/openshift-apps/greenwave/templates/fedora.yaml
  +++ b/roles/openshift-apps/greenwave/templates/fedora.yaml
  @@ -84,6 +84,9 @@ rules:
  --- !Policy
  id: "no_requirements_testing"
  product_versions:
  +  - fedora-33-modular
  +  - fedora-33-containers
  +  - fedora-33-flatpaks
    - fedora-32-modular
    - fedora-32-containers
    - fedora-32-flatpaks
  @@ -107,6 +110,9 @@ rules: []
  --- !Policy
  id: "no_requirements_for_stable"
  product_versions:
  +  - fedora-33-modular
  +  - fedora-33-containers
  +  - fedora-33-flatpaks
    - fedora-32-modular
    - fedora-32-containers
    - fedora-32-flatpaks
  @@ -133,6 +139,7 @@ id: "openqa_release_critical_tasks_for_testing"
  product_versions:
    - fedora-rawhide
    - fedora-eln
  +  - fedora-33
    - fedora-32
    - fedora-31
    - fedora-30
  @@ -147,6 +154,7 @@ id: "openqa_release_critical_tasks_for_stable"
  product_versions:
    - fedora-rawhide
    - fedora-eln
  +  - fedora-33
    - fedora-32
    - fedora-31
    - fedora-30

更新 Robosignatory 配置
^^^^^^^^^^^^^^^^^^^^^^^^^^^

如下更新infra ansible存储库中的 robosignatory 配置

::

  diff --git a/roles/robosignatory/templates/robosignatory.toml.j2 b/roles/robosignatory/templates/robosignatory.toml.j2
  index 16a6708..68f4251 100644
  --- a/roles/robosignatory/templates/robosignatory.toml.j2
  +++ b/roles/robosignatory/templates/robosignatory.toml.j2
  @@ -259,8 +259,8 @@ handlers = ["console"]
              type = "modular"
  
              [[consumer_config.koji_instances.primary.tags]]
  -            from = "f33-modular-updates-candidate"
  -            to = "f33-modular"
  +            from = "f33-modular-signing-pending"
  +            to = "f33-modular-updates-testing-pending"
              key = "{{ (env == 'production')|ternary('fedora-33', 'testkey') }}"
              keyid = "{{ (env == 'production')|ternary('9570ff31', 'd300e724') }}"
              type = "modular"

运行 playbook
^^^^^^^^^^^^^^^^^

::

    $ rbac-playbook openshift-apps/greenwave.yml
    $ rbac-playbook openshift-apps/bodhi.yml
    $ rbac-playbook groups/bodhi-backend.yml
    $ rbac-playbook groups/releng-compose.yml
    $ rbac-playbook manual/autosign.yml

Greenwave 在 OpenShift 中运行(正如playbook路径所暗示的)，因此当playbook完成时，更改不会立即生效。您可以监视
https://greenwave-web-greenwave.app.os.fedoraproject.org/api/v1.0/policies 以等待新策略出现 (这应该需要几分钟时间)。

重新启动bodhi服务
^^^^^^^^^^^^^^^^^^^^^^

重新启动 bodhi 服务以了解 bodhi-backend01 上的bodhi新版本
(查看 https://docs.pagure.org/releng/sop_bodhi_activation.html#action 中的警告，错误为 https://github.com/fedora-infra/bodhi/issues/2177)

::

  $ sudo systemctl restart bodhi-celery
  $ sudo systemctl restart fm-consumer@config
  $ sudo systemctl restart koji-sync-listener

发送公告
^^^^^^^^^^^^^^^^^

关于Bodhi激活的电子邮件 **devel-announce** 和 **test-announce** 列表。
请在下面找到电子邮件的正文：

::

  Hi all, 

  Today's an important day on the Fedora 25 schedule[1], with several significant cut-offs. First of all today is the Bodhi activation point [2]. That means that from now all Fedora 25 packages must be submitted to updates-testing and pass the relevant requirements[3] before they will be marked as 'stable' and moved to the fedora repository. 

  Today is also the Alpha freeze[4]. This means that only packages which fix accepted blocker or freeze exception bugs[5][6] will be marked as 'stable' and included in the Alpha composes. Other builds will remain in updates-testing until the Alpha release is approved, at which point the Alpha freeze is lifted and packages can move to 'stable' as usual until the Beta freeze.

  Today is also the Software String freeze[7], which means that strings marked for translation in Fedora-translated projects should not now be changed for Fedora 25. 

  Finally, today is the 'completion deadline' Change Checkpoint[8], meaning that Fedora 25 Changes must now be 'feature complete or close enough to completion that a majority of its functionality can be tested'. 

  Regards 
  <your_name>

  [1] https://fedorapeople.org/groups/schedule/f-34/f-34-key-tasks.html
  [2] https://fedoraproject.org/wiki/Updates_Policy#Bodhi_enabling 
  [3] https://fedoraproject.org/wiki/Updates_Policy#Branched_release 
  [4] https://fedoraproject.org/wiki/Milestone_freezes 
  [5] https://fedoraproject.org/wiki/QA:SOP_blocker_bug_process 
  [6] https://fedoraproject.org/wiki/QA:SOP_freeze_exception_bug_process 
  [7] https://fedoraproject.org/wiki/ReleaseEngineering/StringFreezePolicy 
  [8] https://fedoraproject.org/wiki/Changes/Policy

验证
============
.. Provide a method to verify that the action completed as expected (success)

对比 koji 标签结构与旧版本

::

  $ koji list-tag-inheritance <branched_release> --reverse
  $ koji list-tag-inheritance <latest_stable_release> --reverse

对比 bodhi 版本与旧版本

::

  $ bodhi releases info <branched_release>
  $ bodhi releases info <latest_stable_release>

检查其他变体，如 modular, 容器和 flatpaks

运行之前请考虑
=======================
.. Create a list of things to keep in mind when performing action.

此时没有其他考虑。文档git存储库仅是静态HTML托管空间，如果有必要，我们可以重新呈现文档并再次推送到存储库。

.. _Mass Branching: https://docs.pagure.org/releng/sop_mass_branching.html 

