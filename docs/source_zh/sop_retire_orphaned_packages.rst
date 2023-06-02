.. SPDX-License-Identifier:    CC-BY-SA-3.0


========================
停用孤立软件包
========================

说明
===========

在 `功能冻结/分支`_ 发布工程之前的每个版本都会停用 `孤立的软件包`_ 。这样可以排除没有所有者的软件并防止未来出现问题。

操作
======
孤立过程分阶段进行：

#. 检测孤立项列表以及删除孤立项时将中断的依赖项。
#. 将潜在孤立名单发送给 devel@lists.fedoraproject.org 以供社区审查并从孤立名单中删除。
#. 停用没有人愿意采用的软件包。

检测孤立项
-----------------

名为 ``find_unblocked_orphans.py`` 的脚本有助于检测过程。它应该在安装了 ``koji`` 和 ``python-fedora``
的计算机上运行。它在没有选项的情况下运行，需要一段时间才能完成。

``find_unblocked_orphans.py`` 在 `发布工程 git 仓库`_ 中可用

宣布将停用的包
---------------------------------

``find_unblocked_orphans.py`` 在命令行上以适合电子邮件正文的形式将文本输出到 stdout。

::

    $ ./find-unblocked-orphans.py > email-message

至少在功能冻结前一个月将输出通过电子邮件发送到开发列表  (``devel@lists.fedodraproject.org``)
，根据需要发送包含更新列表的邮件。这使维护者有机会选择对他们很重要或其他软件包所需的孤立软件包。

停用孤立软件包
----------------

一旦维护者有机会接手孤立的软件包
，剩下的 `软件包就会被退役`_ 。

Bugs
^^^^
此过程可能会为已停用的软件包留下未解决的错误。处理这些不在发布工程的范围内。如果关闭了错误，则只有针对 Rawhide 的错误才会受到影响，因为其他分支可能仍在维护中。

验证
============
若要验证包是否已正确阻塞，我们可以使用
``latest-pkg`` ``koji`` 操作。

::

    $ koji latest-pkg dist-f21 wdm

这应该不返回任何内容，因为 ``wdm`` 包被阻塞。

运行之前考虑
=======================
通常，我们会停用任何不会留下损坏依赖项的内容。如果存在孤立项，其删除将导致依赖项中断，则应向 ``devel@lists.fedoraproject.org`` 和每个依赖包的
``<package>-owner@fedoraproject.org`` 发送第二个警告。

再留出几天时间让维护者注意并修复这些软件包，这样软件包存储库就可以在不损坏依赖或需要软件包的情况下进行维护。在我们的软件包存储库中存在损坏的软件包依赖项是不好的，因此应尽一切努力查找所有者或修复损坏的依赖项。

.. _功能冻结/分支: https://fedoraproject.org/wiki/Schedule
.. _孤立的软件包:
    https://fedoraproject.org/wiki/Orphaned_package_that_need_new_maintainers
.. _发布工程 git 仓库: https://pagure.io/releng
.. _软件包就会被退役:
    https://fedoraproject.org/wiki/How_to_remove_a_package_at_end_of_life
