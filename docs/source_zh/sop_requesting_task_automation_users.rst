.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
请求自动化用户
===========================

.. _sop_requesting_task_automation_user:

说明
===========

在使用 :ref:`RelEng
Automation <_releng-automation>` 执行自动发布工程任务时，有时您会发现需要使用 ``sudo`` 在基础设施中执行某个操作，但该操作尚未与自动化用户相关联。

操作
========

请求一个新的 loopabull_ 用户
--------------------------------

向 `Fedora Infrastructure
<https://pagure.io/fedora-infrastructure/>`_ 提交工单，确保满足以下要求：


* 为需要这些权限提供理由（您要做什么以及为什么？）
* 需要使用 sudo 运行的命令
* 需要在上面运行命令的目标服务器
* 请求为此 OR 创建的 ``loopabull_`` 用户名，或者该
  ``loopabull_`` 用户名需要增强其预先存在的权限

供参考： `Example Infrastructure Ticket
<https://pagure.io/fedora-infrastructure/issue/5943>`_


.. _loopabull: loopabull