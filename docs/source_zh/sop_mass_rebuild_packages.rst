.. SPDX-License-Identifier:    CC-BY-SA-3.0


============
批量重建
============

说明
===========

在开发周期中，我们会定期对rawhide进行批量重建。本SOP将概述执行此操作所需的步骤。

假设
===========
假设批量重建已经通过版本工程和FESCo获得批准并安排好了时间。协调基础设施团队以进行必要的Koji更新。

还假设批量重建不需要按依赖顺序进行，并且批量重建不涉及ABI更改。

注意事项
==============

* 在进行批量重建时，最重要的是要清楚地传达正在执行的操作和重建的状态。
* 检查脚本的进度频率以避免长时间停滞的命令导致批量重建延迟完成。
* 与次要架构进行沟通，确认它们是否与主要架构保持足够的更新状态，当次要架构更新时，创建重建标签和目标。然后它将负责在适当的kojis中重建架构特定的软件包。

操作
=======

准备步骤
-----------------
以下步骤可能会在计划的批量重建之前的几周内完成。

#. 创建批量重建 Pagure Issue

    在 `Release Engineering issues page`_ 上创建一个issue，指向当前发布的时间表。

    参阅 `the Fedora 27 mass rebuild issue example`_.
   
#. 设置批量重建的 Wiki 页面

    批量重建wiki页面应为维护人员回答以下问题：

    * 为什么要进行批量重建
    * 如何选择退出批量重建

    .. note::
   
        请参阅 `the Fedora 26 Wiki example`_.

#. 发出批量重建通知

    将发布在wiki上的相同信息发送到
    `devel-announce@lists.fedoraproject.org` 邮件列表。

    .. note::

         请参阅 `the Fedora 26 e-mail example`_.

#. 创建包含批量重建的标签

    批量重建需要自己的标签来包含所有相关的构建。该示例假设我们正在为Fedora 26进行重建。

    ::

        $ koji add-tag f26-rebuild --parent f26

#. 为新的批量重建标签请求包自动签名

    向 `Fedora Infrastructure`_ 提交工单，请求为包自动签名启用新的批量重建标签。

#. 为批量重建创建Koji标签

    使用上一示例中相同的 `f26-rebuild` 标签：

    ::

        $ koji add-target f26-rebuild f26-build

    .. note::

        **koji add-target** *target-name* *buildroot-tag* *destination-tag*
        描述了上面的语法格式。如果没有指定 *destination-tag* ，那么它将与 *target-name* 相同。


#. 更新脚本

    批量重建依赖于
    `releng git repository`_ 中的四个主要脚本。每一个都需要对每个新的批量重建周期的变量进行一些更改。

    * mass-rebuild.py
        * buildtag
        * targets
        * epoch
        * comment
        * target
    * find-failures.py
        * buildtag
        * desttag
        * epoch
    * mass-tag.py
    * need-rebuild.py
        * buildtag
        * target
        * updates
        * epoch

更改以下项目：

* build标签、holding标签和target标签应该更新，以反映您正在为之构建的Fedora版本
* 应该将 ``epoch`` 更新到所有目标功能在构建系统中均已完成 (并已完成与这些功能相关的 newRepo 任务)的时间点。
* 插入到spec更改日志中的注释


开始批量重建
-------------------------
``mass-rebuild.py`` 脚本负责：

* 发现 koji 中的可用包
* 裁剪掉已经重新构建过的软件包。
* 从 Git 检出软件包
* 提升 spec 文件版本号
* 提交更改
* git 标记更改
* 将构建请求提交到 Koji


#. 连接到 mass-rebuild 机器

    ::

        $ ssh branched-composer.phx2.fedoraproject.org


#. 启动一个终端复用器

    ::

        $ tmux

#. 克隆或下载 `releng git repository`_ 的最新副本。

#. 从 *releng/scripts* 目录下运行 mass-rebuild.py 脚本

    ::

        $ cd path/to/releng_repo/scripts
        $ ./mass-rebuild.py 2>&1 | tee ~/massbuild.out

监控批量重建
------------------------
社区非常关心重建的状态，许多维护者希望能够立即知道他们的构建是否失败。 
``find-failures.py`` 和 ``need-rebuild.py`` 脚本旨在更新供利益相关者监视的公共可用URL。

#. 连接到Compose Machine

    ::

        $ ssh compose-x86-02.phx2.fedoraproject.org

#. 启动一个终端复用器

    ::

        $ tmux

#. 克隆或检出 `releng git repository`_ 的最新副本

#. 设置重新构建失败通知网站
    ``find_failures.py`` 脚本可以发现构建失败的尝试。它会列出这些失败的构建并按软件包所有者排序。

    ::

        $ while true; do ./find_failures.py > f26-failures.html && cp f26-failures.html /mnt/koji/mass-rebuild/f26-failures.html; sleep 600; done

#. 在终端仿真器中启动第二个窗格

#. 设置需要重建软件包的站点
    ``need-rebuild.py`` 脚本可以发现还未重建的软件包，并生成一个html文件，按软件包所有者排序列出它们。这可以让外部利益相关者大致了解大规模重新构建中还有多少工作需要完成。

    ::

        $ while true; do ./need-rebuild.py > f26-need-rebuild.html && cp f26-need-rebuild.html /mnt/koji/mass-rebuild/f26-need-rebuild.html; sleep 600; done

大规模重新构建后的任务
-----------------------
一旦批量重建脚本完成，并且所有挂起的构建都已完成，则需要对这些构建进行标记。 ``mass-tag.py`` 脚本将完成此任务。脚本将：

* 发现已完成的构建
* 为给定包裁剪比最新版本旧的版本
* 将剩余构建标记到其最终目的地 (不生成电子邮件)

#. 克隆或检出 `releng git repository`_ 的最新副本

#. 运行 ``mass-tag.py`` 脚本 (需要 koji kerberos 身份验证)

    ::

        $ cd path/to/releng_repo/scripts
        $ ./mass-tag.py --source f36-rebuild --target f36

#. 将最终通知发送到
   *devel-announce@lists.fedoraproject.org* 列表

    内容应该类似于 `example email`_.

.. _the Fedora 26 Wiki example: https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild
.. _the Fedora 26 e-mail example: https://lists.fedoraproject.org/archives/list/devel-announce@lists.fedoraproject.org/message/QAMEEWUG7ND5E7LQYXQSQLRUDQPSBINA/
.. _releng git repository: https://pagure.io/releng
.. _Release Engineering issues page: https://pagure.io/releng/issues
.. _example email: https://lists.fedoraproject.org/archives/list/devel@lists.fedoraproject.org/message/QAMEEWUG7ND5E7LQYXQSQLRUDQPSBINA/
.. _Fedora Infrastructure: https://pagure.io/fedora-infrastructure/issues
.. _the Fedora 27 mass rebuild issue example: https://pagure.io/releng/issue/6898
