.. SPDX-License-Identifier:    CC-BY-SA-3.0


========================
弃用FTBFS软件包
========================

说明
===========

.. note::
    FTBFS = "Fails To Build From Source"，无法从源码构建

在功能冻结之前的每个版本，我们都会弃用FTBFS的所有软件包。这将不再从源代码构建的软件拒之门外，并防止未来出现问题。

操作
======
FTBFS过程分阶段进行：

#. 检测FTBFS包的列表以及如果删除这些包将被破坏的依赖项。
#. 将可能不推荐使用的FTBFS包的列表发送到
   devel@lists.fedoraproject.org 以供社区审查，并通过修复程序包将其从FTBFS列表中删除。
#. 从Fedora软件包仓库中删除已确认为FTBFS的软件包。

检测FTBFS
---------------

我们将删除至少两个发布周期内未能构建的包。例如，在为Fedora 21分支做准备时，自Fedora 19循环以来FTBFS的包 (即dist标签为fc18或更早的包) 将被视为删除的候选包。调整 `find_FTBFS.py`_
并运行它以获得候选包的列表。

给定上面的候选列表，rel-eng应该尝试使用koji构建每个候选包。如果包构建现在成功，则该包可能会从候选列表中删除。

宣布弃用软件包
------------------------------------

至少在功能冻结前一周通过电子邮件将输出发送到开发列表 (``devel@lists.fedodraproject.org``)。这使维护人员有机会修复对他们来说很重要的包。必要时对清单进行跟进。

注销FTBFS软件包
-----------------------

一旦维护人员有机会拿起并修复FTBFS包，剩下的包就被 ``retired`` 屏蔽，并用git创建 ``dead.package`` 文件。

GIT和包数据库Package DB
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
所需权限：GIT的provenpackage，Package DB的cvsadmin。

我们只需要从 ``rawhide`` 分支中删除现有的文件，并将其替换为 ``dead.package`` 文件，该文件的内容描述了包为何已失效。此外，需要在Package DB中将包标记为已退役。Fedpkg负责处理此问题：

例如，如果我们希望为roxterm包清理git，我们会：

::

    $ fedpkg clone roxterm
    $ cd roxterm
    $ fedpkg retire "Retired on $(date -I), because it failed to build for two releases (FTBFS Cleanup)."

Koji
^^^^

所需权限：如果自动blocking失败，则需要koji管理员。

Blocking应该在PackageDB中的包退役后几分钟自动发生。如果没有，则使用 ``block-pkg`` ``koji`` 命令进行阻塞。

Koji接受多个包名称作为输入，因此我们可以使用FTBFS包列表作为输入。不推荐的程序包仅被最新的
``f##`` 标记阻塞。例如，如果我们在Fedora 21的开发过程中从rawhide中想要 ``deprecate`` (block) ``sbackup,
roxterm,`` 和 ``uisp`` ，我们将运行以下命令：

::

    $ koji block-pkg f21 sbackup roxterm uisp

Bugs
^^^^

此过程可能会为不推荐使用的包留下未解决的错误。处理这些问题不在宽松的范围内。如果Bug被关闭，那么只有针对Rawhide的Bug才会受到影响，因为其他分支可能仍在维护。

验证
============
为了验证包是否被正确阻塞，我们可以使用
``latest-pkg`` ``koji`` 操作。

::

    $ koji latest-pkg dist-f16 wdm

这应该不会返回任何内容，因为 ``wdm`` 程序包已被阻止。

还要检查package DB是否显示包已失效，并且rawhide分支仅包含一个dead.package文件。

运行之前请考虑
=======================

一般来说，我们会阻塞任何不会留下破碎依赖关系的东西。如果删除某些包会导致依赖关系中断，则应为每个依赖包发送第二个警告给 devel@lists.fedoraproject.org 和
<package>-owner@fedoraproject.org。

再给维护人员几天时间，让他们注意并修复这些包，这样包仓库就可以在不破坏依赖关系或不需要弃用包的情况下进行维护。在我们的包仓库中有损坏的包依赖关系是不好的，所以应该尽一切努力找到所有者或修复损坏的依赖关系。


.. _FTBFS: https://fedoraproject.org/wiki/Fails_to_build_from_source
.. _find_FTBFS.py: https://pagure.io/releng/blob/main/f/scripts/find_FTBFS.py
