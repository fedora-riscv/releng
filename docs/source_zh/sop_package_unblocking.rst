.. SPDX-License-Identifier:    CC-BY-SA-3.0


==================
解封软件包
==================

说明
===========
软件包有时会从 Fedora 中解封，通常是在软件包被孤立并且现在有了新的所有者时。发生这种情况时，发布工程需要从 koji 标签中“解锁”包。

操作
======

查找解封请求
---------------------

解封请求通常在 `rel-eng issue tracker`_ 中报告。

执行解封
----------------------

首先将工单分配给自己以显示您正在处理请求。

发现解封的适当位置
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
工单应该告诉你解锁哪个 Fedora 版本的软件包。通常它会说“Fedora 13”或“F14”。这意味着我们需要在 Fedora 级别和所有未来的标签上解锁它。但是，根据软件包被阻塞的位置，我们可能必须在不同的 Fedora 级别执行解封操作。

若要发现包被阻塞的位置，请使用 koji 的 ``list-pkgs`` 方法。

::

    $ koji list-pkgs --help
    Usage: koji list-pkgs [options]
    (Specify the --help global option for a list of other help options)

    Options:
      -h, --help         show this help message and exit
      --owner=OWNER      Specify owner
      --tag=TAG          Specify tag
      --package=PACKAGE  Specify package
      --quiet            Do not print header information
      --noinherit        Don't follow inheritance
      --show-blocked     Show blocked packages
      --show-dups        Show superseded owners
      --event=EVENT#     query at event
      --ts=TIMESTAMP     query at timestamp
      --repo=REPO#       query at event for a repo

例如，如果我们想看看python-psco在哪里被阻塞，我们会这样做：

::

    $ koji list-pkgs --package python-psyco --show-blocked
    Package                 Tag                     Extra Arches     Owner          
    ----------------------- ----------------------- ---------------- ---------------
    python-psyco            dist-f14                                 konradm         [BLOCKED]
    python-psyco            olpc2-ship2                              shahms         
    python-psyco            olpc2-trial3                             shahms      
    ...

在这里我们可以看到它在 dist-f14 被阻塞了。如果我们收到请求要求在 f14 之前解封，我们可以简单地使用 dist-f14 目标来解封。但是，如果他们希望在 f14 之后解锁，我们会使用用户要求的最早的 dist-f？？标签，例如如果用户要求在 Fedora 15+ 中解封它，则会使用 dist-f15

正在执行解封
^^^^^^^^^^^^^^^^^^^^^^

若要解封一个标签的包，请使用 Koji 的 ``unblock-pkg`` 方法。

::

    $ koji unblock-pkg --help
    Usage: koji unblock-pkg [options] tag package [package2 ...]
    (Specify the --help global option for a list of other help options)

    Options:
      -h, --help  show this help message and exit

例如，如果我们被要求在 F14 中解封 python-psyco，我们将发出：

::

    $ koji unblock-pkg dist-f14 python-psyco

现在可以关闭工单了。

验证
============
要验证包是否已成功解除阻塞，请使用 ``list-pkgs``
koji 命令：

::

    $ koji list-pkgs --package python-psyco --show-blocked

我们应该看到在 dist-f14 或更高版本处列出的包未被阻塞：


::

    Package                 Tag                     Extra Arches     Owner          
    ----------------------- ----------------------- ---------------- ---------------
    python-psyco            olpc2-trial3                             jkeating       
    python-psyco                   olpc2-ship2                              jkeating       
    python-psyco                   olpc2-update1                            jkeating       
    python-psyco                   trashcan                                 jkeating       
    python-psyco                   f8-final                                 jkeating       
    ...

我们不应该看到它在 dist-f14 或任何后来的 Fedora 标签中被列为阻塞。

运行之前请考虑
=======================
* 观看第二天的 rawhide/branched/任何报告，了解与软件包相关的损坏。我们可能必须重新阻塞软件包才能修复deps。

.. _rel-eng issue tracker:
    https://pagure.io/releng/issues
