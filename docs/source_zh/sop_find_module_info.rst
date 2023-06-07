.. SPDX-License-Identifier:    CC-BY-SA-3.0


==========================
查找模块信息
==========================

说明
===========
当用户将构建提交到模块构建服务 （MBS） 时，它会依次将构建提交到 Koji。有时，您正在查看一个 koji 构建，并且您想知道它是哪个模块构建的一部分。

注意事项
==========

它要求构建已完成并已标记，直到
https://pagure.io/fm-orchestrator/issue/375 完成。

设置
=====

运行以下命令::

    $ sudo dnf install python-arrow python-requests koji

操作
======

运行以下命令::

    $ scripts/mbs/koji-module-info.py $BUILD_ID
