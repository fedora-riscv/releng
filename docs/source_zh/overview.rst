.. SPDX-License-Identifier:    CC-BY-SA-3.0


.. _overview:

===================================
Fedora 发布工程概述
===================================

.. _overview-intro:

介绍
============

Fedora 的开发过程非常开放，涉及到1000多个软件包维护者（还有测试人员、翻译人员、文档撰写人员等等）。这些维护者负责 Fedora 分发的大部分开发工作。一个由选举产生的 `委员会`_ 为项目的工程方面提供了一定程度的指导。

Fedora 开发的快速节奏留给开发系统很少的时间来制作质量可靠的版本。为了解决这个问题，Fedora 项目采用了定期冻结和发布分销版的里程碑（Alpha、Beta、Final）以及分支开发树以维护不同的开发线路。

每个 Fedora 发行版都有稳定的分支树和关联的 `存储库`_ 。 `Rawhide`_  是任何 Fedora 开发的起点和所有分支发散的主干。在将其发送为稳定版本之前，发行版将从 Rawhide `分支`_ ，里程碑版本（Alpha、Beta 和 Final）均是从这些分支树构建而成。

各种类型的每夜快照图像都是从 Rawhide 和 Branch 构建（如果存在）并从 `mirrors`_ 或 `Koji`_ 构建系统中提供下载。

`Fedora 发布生命周期`_ 页面是更详细了解这些过程的好入口。关于 Fedora 发布过程的其他一些有用参考资料包括：

* `发布规划过程
  <https://fedoraproject.org/wiki/Changes/Policy>`_
* `发布验证测试计划
  <https://fedoraproject.org/wiki/QA:Release_validation_test_plan>`_
* `更新测试过程
  <https://fedoraproject.org/wiki/QA:Updates_Testing>`_，通过
  `Bodhi <https://fedoraproject.org/wiki/Bodhi>`_ 和
  `更新政策 <https://fedoraproject.org/wiki/Updates_Policy>`_
* `测试组合和发布候选系统
  <https://fedoraproject.org/wiki/QA:SOP_compose_request>`_
* `阻止程序错误进程
  <https://fedoraproject.org/wiki/QA:SOP_blocker_bug_process>`_
  和
  `冻结异常错误进程
  <https://fedoraproject.org/wiki/QA:SOP_freeze_exception_bug_process>`_
* `存储库`_
* `Bugzilla 系统
  <https://fedoraproject.org/wiki/Bugs_and_feature_requests>`_

最终版本清单
=======================

在最终的 Fedora 发布之前需要完成各种任务。发布工程负责其中的许多，如此处所述。

发布公告
--------------------

`Fedora 文档项目`_ 为最终版本准备发布公告。需要在最终发布日期前两周提交一个 `bug 报告`_ 。

镜像列表文件
-----------------

需要为新的发行版创建一组镜像列表文件。请给 `Fedora 镜像管理员`_ 发送电子邮件以创建这些文件。这些镜像列表文件应该在 Final Freeze 时创建，但可能会重定向到 Rawhide，直到最终位已经准备就绪。

发布组合
=================

任何拥有适当架构和访问软件包仓库的快速计算机的人都可以构建 Fedora“发行版”。构建发行版所需的所有工具都可以从软件包仓库中获取。这些工具旨在提供一种一致的方式来构建 Fedora 发行版。
实际上，只需要几个命令就可以构建完整的发行版，其中包括创建网络安装映像、离线安装映像（'DVD'）、实时映像、磁盘映像、安装存储库、[[FedUp]]升级映像和其他一些程序。这些命令被命名为 pungi 和 livecd-creator。

.. note::
    目前正在开展工作，用 livecd-creator 取代
    `livemedia-creator`_ 。

Pungi
-----

`Pungi`_ 是用于组合 Fedora 发行版的工具。它需要在它所组织的软件包集的 chroot 环境中运行。这样可以确保使用正确的用户空间工具来匹配将用于执行安装的内核。
它使用 comps 文件和 yum 仓库来收集组织所需的软件包。 `Koji`_ 构建系统提供了在各种架构的 chroot 环境中运行任务并能够从特定集合中生成软件包的 yum 仓库的方法。

Livecd-creator
--------------

Livecd-creator 是 Fedora 中的 `livecd-tools`_ 软件包的一部分，它用于在 Fedora 发行版中组合实时映像。它还用于组合许多自定义 `Spins`_ 或 Fedora 的变体。

分发
============

一旦组合完成，就需要将组合的发行版媒体、安装树和冻结的 `存储库`_ 与 Fedora 镜像系统进行同步。[[MirrorManager]]提供了镜像系统的更多详细信息。许多映像还通过 BitTorrent 提供作为另一种下载方法。

下载镜像
----------------

如果需要私有化填充 Fedora 镜像系统和基础设施，则需要取决于其本身。

BitTorrent
----------

BitTorrent 目前由 http://torrent.fedoraproject.org 提供服务。映像通过此 `标准操作程序
<https://infrastructure.fedoraproject.org/infra/docs/docs/sysadmin-guide/sops/torrentrelease.rst>`_ 添加到系统中。

致谢
================

本文档受到 `FreeBSD <http://freebsd.org>`_  `发布工程文档
<http://www.freebsd.org/doc/en_US.ISO8859-1/articles/releng/article.html>`_ 的影响。

.. _委员会: https://fedoraproject.org/wiki/Fedora_Engineering_Steering_Committee
.. _存储库: https://fedoraproject.org/wiki/存储库
.. _Rawhide: https://fedoraproject.org/wiki/Releases/Rawhide
.. _分支: https://fedoraproject.org/wiki/Releases/Branched
.. _mirrors: https://mirrors.fedoraproject.org/
.. _Koji: https://fedoraproject.org/wiki/Koji
.. _PDC: https://pdc.fedoraproject.org/
.. _Fedora 发布生命周期: https://fedoraproject.org/wiki/Fedora_Release_Life_Cycle
.. _Fedora 文档项目: https://fedoraproject.org/wiki/Docs_Project
.. _bug 报告:
    https://bugzilla.redhat.com/bugzilla/enter_bug.cgi?product=Fedora%20Documentation&op_sys=Linux&target_milestone=---&bug_status=NEW&version=devel&component=release-notes&rep_platform=All&priority=normal&bug_severity=normal&assigned_to=relnotes%40fedoraproject.org&cc=&estimated_time_presets=0.0&estimated_time=0.0&bug_file_loc=http%3A%2F%2F&short_desc=RELNOTES%20-%20Summarize%20the%20release%20note%20suggestion%2Fcontent&comment=Provide%20details%20here.%20%20Do%20not%20change%20the%20blocking%20bug.&status_whiteboard=&keywords=&issuetrackers=&dependson=&blocked=151189&ext_bz_id=0&ext_bz_bug_id=&data=&description=&contenttypemethod=list&contenttypeselection=text%2Fplain&contenttypeentry=&maketemplate=Remember%20values%20as%20bookmarkable%20template&form_name=enter_bug 
.. _Fedora 镜像管理员: mailto:mirror-admin@fedoraproject.org
.. _livemedia-creator: https://github.com/rhinstaller/lorax/blob/master/src/sbin/livemedia-creator
.. _Pungi: https://pagure.io/pungi
.. _livecd-tools: https://fedoraproject.org/wiki/FedoraLiveCD
.. _Spins: https://spins.fedoraproject.org
