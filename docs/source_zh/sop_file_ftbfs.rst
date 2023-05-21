.. SPDX-License-Identifier:    CC-BY-SA-3.0


==========
文件 FTBFS
==========

说明
===========

.. note::
    FTBFS = "Fails To Build From Source，无法从源代码构建"

每次大规模重建后，我们都会为在大规模重建期间未能构建的软件包提交 FTBFS 错误。

这应该在 `大规模重建版本合并到 main 标签`_ 之后运行。

操作
======
FTBFS 错误在 bugzilla 中提交。

#. 为 FTBFS 创建一个bugzilla bug
    * 如果未创建使用 `以前的 FTBFS bugzilla bug 示例`_ 

#. 为 RAWHIDEFTBFS 设置别名
    * 从以前的 FTBFS bugzilla 中删除 RAWHIDEFTBFS 别名
    * 在新的 rawhide 版本 FTBFS bugzilla 上设置 RAWHIDEFTBFS 别名
    * 在 RAWHIDEFailsToInstall bugzilla 上以相同的方式设置别名

#. 在本地计算机上安装 `python-bugzilla-cli` ，如果未安装的话。
    ::

        $ sudo dnf install python-bugzilla-cli

#. 更新 `massrebuildsinfo.py`
    * epoch
    * buildtag
    * destag
    * tracking_bug

    .. note::
        这些值中的大多数已在大规模重建期间更新，可能需要更新的值只有 `tracking_bug`

#. 更新 `mass_rebuild_file_bugs.py`
    * rebuildid

#. 使用 `bugzilla login` 命令在终端中登录 bugzilla
    ::

        $ bugzilla login

    .. note::
        以 `releng@fedoraproject.org` 身份登录

#. 在本地运行 `mass_rebuild_file_bugs.py` 
    ::

        $ python mass_rebuild_file_bugs.py


.. _大规模重建版本合并到 main 标签: https://docs.pagure.org/releng/sop_mass_rebuild_packages.html#post-mass-rebuild-tasks
.. _以前的 FTBFS bugzilla bug 示例: https://bugzilla.redhat.com/show_bug.cgi?id=1750908
