.. SPDX-License-Identifier:    CC-BY-SA-3.0


==================
添加新的发布工程师
==================

说明
====
人们不时自愿（或被指派）做Fedora Release Engineering。本SOP旨在描述添加新发布工程师的过程，
以便他们有权完成任务，知道在哪里可以找到任务，并被介绍给现有成员。有几个组用来
管理对各个系统的访问：

* ``cvsadmin``: pkgdb2的管理组（允许注销/孤立所有包等），允许git通过SSH对dist git中的所有包进行写访问
* ``gitreleng``: 允许写访问以发布工程git仓库
* ``signers``: 成员身份是使用 `sigul`_ 所必需的。
* ``sysadmin``: 允许SSH访问bastion，即PHX2数据中心的SSH网关。只有从这里才能通过SSH访问其他几个内部系统。
* ``sysadmin-cvs``: 允许shell访问pkgs01（pkgs.fedeoraproject.org）
* ``sysadmin-releng``: 允许SSH从bastion访问autosign01、koji03、koji04、releng04、relepel01

操作
======
一名新的发布工程师将访问一系列系统中的权限，并被引入相关小组。

Git
---
Fedora Release Engineering维护一个脚本的git仓库。这可以在 ssh://git@pagure.io/releng.git 的 `Pagure`_ 中找到。对该组的写访问由对“gitreling”FAS组控制。需要将新成员的FAS用户名添加到此组中。

https://pagure.io/releng


``FIXME: walkthrough group addition``

FAS
---
FAS中有一个相关的小组，添加了发布工程师，以便授予他们在Fedora基础设施中的各种权限。需要将新成员的FAS用户名添加到此组中。``

``FIXME: walkthrough group addition``

Koji
----
为了执行某些（取消）标记操作，发布工程师必须是koji中的管理员。要授予用户管理权限，可以使用koji中的 ``grant-permission`` 命令。

::

    $ koji grant-permission --help
    Usage: koji grant-permission <permission> <user> [<user> ...]
    (Specify the --help global option for a list of other help options)

    Options:
      -h, --help  show this help message and exit

例如，如果我们想授予npetrov管理权限，我们将使用：

::

    $ koji grant-permission admin npetrov

Sigul
-----
Sigul是我们的签名服务器系统。如果他们要为一个版本的包签名，他们需要以签名者的身份下注。

有关如何设置Sigul的信息，请参阅： `sigul`_

RelEng 文档页
-------------
新的发布工程师应添加到： `发布工程成员名单 <index-team-composition>`_

rel-eng 电子邮件列表
--------------------
发布工程为发生在我们 `邮件列表`_ 上的垃圾邮件和讨论贴标签。新人需要订阅。

IRC
---
我们要求在Libera上的 `#fedora-releng` 中空闲的发布工程师可供其他基础设施管理员查询。在Libera上的 `#fedora-admin` 上空闲是可选的。虽然有点吵，但人们有时会问releng成员一些相关的问题。

新成员公告
----------
当一个新的releng成员开始加入时，我们会在电子邮件列表中宣布。这让其他管理员知道，他们希望有一个新的名字出现在标签和IRC上。

验证
====

Git
---
您可以通过ssh到设置FAS的系统并使用 ``getent`` 验证gitreleng中的成员身份：
::

    $ ssh fedorapeople.org getent group gitreleng
    gitreleng:x:101647:ausil,dwa,jwboyer,kevin,notting,pbabinca,sharkcz,skvidal,spot

您可以验证新用户是否在上述列表中。

FAS
---
您可以通过ssh到设置FAS的系统并使用 ``getent`` 验证releng组中的成员身份：

::

    $ ssh fedorapeople.org getent group releng
    releng:x:101737:atowns,ausil,dwa,jwboyer,kevin,lmacken,notting,pbabinca,spot

您可以验证新用户是否在上述列表中。

Koji
----
要验证releng成员是否为koji管理员，请使用 ``list-permissions`` koji命令：

::

    $ koji list-permissions --user npetrov
    admin

这表明npetrov是一名管理员。

Sigul
-----
* ``FIXME``

Wiki 页面
---------
验证很容易。看看这一页就知道了。

releng 邮件列表
---------------
通过询问用户是否收到公告电子邮件进行验证

公告电子邮件
------------
见以上

运行之前请考虑
==============
* 确保releng人员牢牢掌握我们所做的任务，以及在遇到困难时在哪里寻求帮助

.. _sigul: https://fedoraproject.org/wiki/Sigul_Client_Setup_SOP
.. _Pagure: https://pagure.io/pagure
.. _邮件列表: https://admin.fedoraproject.org/mailman/listinfo/rel-eng
