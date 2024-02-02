.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
在Bodhi中启用Rawhide
===========================

概述
===========

本SOP涵盖了在Bodhi中启用Rawhide所需的步骤。


在Bodhi中创建release
---------------------------

为了开始在Bodhi中为Rawhide创建更新，需要在Bodhi中创建release。 Bodhi中的Rawhide由Fedora版本（即Fedora 31）表示，但它设置为预发布状态。


增加 koji tags
+++++++++++++++++

::

    $ koji add-tag --parent f31 f31-updates-candidate
    $ koji add-tag --parent f31 f31-updates-testing
    $ koji add-tag --parent f31-updates-testing f31-updates-testing-pending
    $ koji edit-tag --perm autosign f31-updates-testing-pending
    $ koji add-tag --parent f31 f31-updates-pending
    $ koji add-tag --parent f31 f31-override


更改 koji targets
+++++++++++++++++++++++

::

    $ koji edit-target f31 --dest-tag f31-updates-candidate
    $ koji edit-target f31-candidate --dest-tag f31-updates-candidate
    $ koji edit-target rawhide --dest-tag f31-updates-candidate

在Bodhi中创建release
+++++++++++++++++++++++++++

::

    $ bodhi releases create --name "F31" --long-name "Fedora 31" --id-prefix FEDORA --version 31 --branch f31 \
      --dist-tag f31 --stable-tag f31 --testing-tag f31-updates-testing --candidate-tag f31-updates-candidate \
      --pending-stable-tag f31-updates-pending --pending-testing-tag f31-updates-testing-pending \
      --state pending --override-tag f31-override --create-automatic-updates --not-composed-by-bodhi


重要的标志是`--not-composed-by-bodhi`，它告诉bodhi不要在每晚的推送中包括rawhide更新，以及`--pending-automatic-updates`，它告诉bodhi自动创建一个更新侦听koji标签（用pending-testing-tag标记的构建）消息。


Bodhi 配置
+++++++++++++++++++

Bodhi被配置为在Rawhide发布测试中要求零强制天数。
这是在ansible roles/bodhi 2/base/templates/production.ini.j2中完成的，如下所示。

::

    f{{ FedoraRawhideNumber }}.pre_beta.mandatory_days_in_testing = 0


Robosignatory 配置
+++++++++++++++++++++++++++

Robosigniter需要配置为在CI管道测试这些构建之前对rawhide构建进行签名。

::

    {
        "from": "f31-updates-candidate",
        "to": "f31-updates-testing-pending",
        "key": "fedora-31",
        "keyid": "3c3359c4"
    },


Branching Rawhide
-----------------

当到了分支rawhide的时候，应该创建一个新的版本（例如 F32）按照上述步骤。旧的rawhide释放（例如 F31）应该保持配置为rawhide，直到我们为它激活Bodhi（2周后）。要激活旧rawhide上的Bodhi（如 F31）现有的release在Bodhi中应该修改如下。

::
    $ bodhi releases edit --name "F31" --stable-tag f31-updates --no-create-automatic-updates --composed-by-bodhi

Robosignatory 配置
+++++++++++++++++++++++++++

在Bodhi激活时，需要更新Robosignator配置以匹配Bodhi版本的正常配置。

::

    {
        "from": "f31-signing-pending",
        "to": "f31-updates-testing-pending",
        "key": "fedora-31",
        "keyid": "3c3359c4"
    },
