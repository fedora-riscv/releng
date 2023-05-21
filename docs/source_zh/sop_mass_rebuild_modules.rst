.. SPDX-License-Identifier:    CC-BY-SA-3.0


=======================
模块的批量重建
=======================

说明
===========

在开发周期中，我们定期对rawhide模块进行大规模的重建。本SOP将概述执行此操作所需的步骤。

假设
===========
假设批量重建已经通过发布工程和FESCo获得批准和安排，并且与基础设施协调，以进行任何必要的更新。

注意事项
==============

* 在执行批量重建时，最重要的一点就是要清楚地传达正在执行的操作以及重建的状态。
* 经常检查脚本，以避免长时间停止的命令在完成重建过程中造成严重延迟。

操作
=======

准备步骤
-----------------
在完成 `软件包的批量重建`_ 后，应完成以下步骤。

#. 更新脚本

大规模重建依赖于 `releng git repository`_ 中的两个主要脚本。每个脚本在新的批量重建周期中都需要对一些变量进行更改。

    * *mass-rebuild-modules.py*
        * rebuildid
    * *massrebuildsinfo.py*
        * module_mass_rebuild_epoch
        * module_mass_rebuild_platform

更改以下项目：

* 在massrebuildsinfo.py中， ``rebuildid`` 需要匹配您正在大规模重新构建的模块的发行版
* ``module_mass_rebuild_epoch`` 大多数情况下将是软件包大规模重新构建的 epoch
* ``module_mass_rebuild_platform`` 应为 rawhide 模块平台


开始模块的批量重建
------------------------------------
``mass-rebuild-modules.py`` 脚本负责：

* 从PDC中发现可用模块
* 从mbs中找到模块信息，并检查是否在epoch日期之后提交了模块构建
* 从 dist-git 检出模块
* 切换到适当的 stream
* 查找 modulemd 文件
* 使用 libmodulemd 确定此模块流是否适用于此平台版本
* 如果需要重建，则提交更改
* 推送提交
* 通过 mbs 提交构建请求


#. 连接到负责批量重构的机器

    ::

        $ ssh compose-branched01.iad2.fedoraproject.org


#. 启动终端多路复用器

    ::

        $ tmux

#. 克隆或签出 `releng git repository`_ 的最新副本。

#. 从 *releng/scripts* 运行 `mass-rebuild-modules.py` 脚本

    ::

        $ cd path/to/releng_repo/scripts
        $ ./mass-rebuild-modules.py <path_to_token_file> build --wait 2>&1 | tee ~/massbuildmodules.out

.. note::

        令牌文件应位于 infra 的私有 ansible 存储库中，或者要求 infra 使用此 `过程`_ 将其发送给您。

.. note::

        `构建` 选项非常重要，因为模块的批量分支也将使用相同的脚本，只是将 `massrebuildsinfo.py` 中的选项更改为 `branch` 和 `module_mass_branching_platform` 。

批量重建任务后
-----------------------
模块批量重建完成后，向devel-announce@列表发送电子邮件

#. 将最终通知发送到
   *devel-announce@lists.fedoraproject.org* 列表

.. _releng git repository: https://pagure.io/releng
.. _过程: https://pagure.io/fedora-infrastructure/issue/8048#comment-587789
.. _软件包的批量重建: https://docs.pagure.org/releng/sop_mass_rebuild_packages.html
