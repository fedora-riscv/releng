.. SPDX-License-Identifier:    CC-BY-SA-3.0


.. Fedora Release Engineering documentation master file, created by
   sphinx-quickstart on Tue Oct 20 14:43:54 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==========================
Fedora Release Engineering
==========================

目录：

.. toctree::
    :maxdepth: 2

    overview
    philosophy
    contributing
    troubleshooting
    architecture
    sop


本页包含有关 Fedora 发布工程团队的信息。

.. _releng-contact-info:

联系信息
===================
* IRC: ``#fedora-releng`` 在 irc.libera.chat 上
* 邮件列表： `rel-eng@lists.fedoraproject.org <https://admin.fedoraproject.org/mailman/listinfo/rel-eng>`_
* 问题跟踪： `Fedora Releng Pagure Tickets <https://pagure.io/releng/new_issue>`_

如果您希望发布工程团队完成某些事情（例如，将软件包移动到buildroot或冻结的合成中），请在上面提到的问题跟踪器中创建工单。请在相应的文本框中输入您的FAS用户名或电子邮件地址，以确保团队可以与您联系。

.. _index-team-composition:

团队组成
================

* `Mohan Boddu (mboddu) <https://fedoraproject.org/wiki/User:mohanboddu>`_ (Lead)
* `Dennis Gilmore (dgilmore) <https://fedoraproject.org/wiki/User:Ausil>`_
* `Kevin Fenzi (nirik) <https://fedoraproject.org/wiki/User:kevin>`_
* `Till Maas (tyll) <https://fedoraproject.org/wiki/User:till>`_
* `Jon Disnard (masta) <https://fedoraproject.org/wiki/User:parasense>`_
* `Dan Horák (sharkcz) <https://fedoraproject.org/wiki/User:sharkcz>`_ (secondary arches)
* `Peter Robinson (pbrobinson) <https://fedoraproject.org/wiki/User:pbrobinson>`_
* `Adam Miller (maxamillion) <https://fedoraproject.org/wiki/User:maxamillion>`_
* `Patrick Uiterwijk (puiterwijk) <https://fedoraproject.org/wiki/User:puiterwijk>`_
* `Ralph Bean (threebean) <https://fedoraproject.org/wiki/User:ralph>`_
* Kellin (Kellin)

发布团队成员由 FESCo 批准。但是，FESCo 已将此权力委托给发布团队本身。如果您想加入团队，请阅读 :ref:`join-releng` 。

什么是 Fedora 发布工程？
===================================

有关概述，请参阅 :doc:`overview <overview>`.

为什么我们以我们的方式做事
===================================

有关 Fedora 发布工程理念的信息，请参阅
:doc:`philosophy <philosophy>`.

Fedora 发布工程领导
=====================================

Mohan Boddu (mboddu on IRC, FAS 用户名 mohanboddu)

领导层目前由 FESCo 任命，并听取当前发布团队的意见。

我们做的事情
============

* 创建官方 Fedora 版本。
    * Fedora 产品
        * Cloud
        * Server
        * Workstation
    * Fedora Spins
* 报告从 `branched`_ 创建开始发布的进度。
* 向 FESCo 报告流程更改。
* 如果已知某些内容有争议，我们会在实施之前告知 FESCo，否则实施通常与报告同时进行。
* 制定冻结管理政策
* 管理构建系统
* 从 Fedora 中删除未维护的软件包
* 推送更新的包
* 编写和维护工具来组合和推送 Fedora


.. _join-releng:

加入发布工程
===========================

rel-eng 的大部分沟通是通过 IRC 进行的。最好的方法之一是参加其中一个会议，并在会议的开放时间说出你有兴趣在结束时做一些工作。如果你不能参加会议，你也可以在IRC上与我们联系或者注册
`邮件列表 <https://admin.fedoraproject.org/mailman/listinfo/rel-eng>`_ 。

由于发布工程需要特殊的访问权限才能访问 Fedora 的重要系统，因此新加入 rel-eng 的人通常会逐步获得访问权限。例如，通常人们不会立即获得签署软件包和推送更新的能力。你可以从以下一些任务开始：调查构建失败的原因（如果 rel-eng 能够采取措施来解决）并帮助编写各种 rel-eng 任务的脚本。

Fedora 发布工程还使用和依赖许多工具，努力改进这些工具的上游，以促进 Fedora 项目正在努力实现的新功能也是加入 Fedora Rel-Eng 的好方法之一。

我们如何做
============

请参阅我们的 :doc:`标准操作程序 <sop>` ，详细了解我们如何做我们所做的事情。

大多数关于发布工程的讨论将在
`#fedora-releng` 或 releng 邮件列表中进行。如有要求，请查阅联系信息 :ref:`releng-contact-info`

会议
========
rel-eng 每周一 14:30 UTC 在 Libera IRC 网络上的 `#fedora-meeting-2` 举行例会。

* `会议议程 <https://pagure.io/releng/issues?status=Open&tags=meeting>`_ 是根据包含会议关键字的 pagure 中的开放工单创建的。

会议纪要
---------------
会议记录发布到 rel-eng 件列表中。它们也可以在
`releng Meetbot 团队页面
<https://meetbot.fedoraproject.org/sresults/?group_id=releng&type=team>`_ 上找到

还有 `2007-04-16 到 2009-05-04 的历史会议纪要
<https://fedoraproject.org/wiki/ReleaseEngineering/Meetings>`_ 。

当前活动
==================

请参阅我们的 `看板`_ ，了解正在进行的项目工作。

请参阅我们的 `工单队列 <https://pagure.io/releng/issues>`_ ，了解我们目前正在做的事情。

有关 Fedora 版本的信息，包括时间表，请参阅 `Releases <https://fedoraproject.org/wiki/Releases>`_ 。

冻结策略
===============

* `里程碑 (Alpha, Beta, Final) 冻结 <https://fedoraproject.org/wiki/Milestone_freezes>`_
* `String 冻结策略`_ (与 alpha 冻结相同)
* `更改冻结策略 <https://fedoraproject.org/wiki/Changes/Policy>`_
  (即“feature”中的“Change”)
* `更新政策 <https://fedoraproject.org/wiki/Updates_Policy>`_
  (不是技术性冻结，而是兴趣)

索引和表
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _branched: https://fedoraproject.org/wiki/Releases/Branched
.. _看板:
    http://taiga.fedorainfracloud.org/project/acarter-fedora-docker-atomic-tooling/kanban
.. _String 冻结策略:
    https://fedoraproject.org/wiki/Software_String_Freeze_Policy
