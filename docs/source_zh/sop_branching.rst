.. SPDX-License-Identifier:    CC-BY-SA-3.0


====
分支
====

说明
====
本SOP涵盖了如何为包建立git和pkgdb分支，无论是针对已通过审查的新包，还是针对需要新分支的现有包（例如EPEL）。Release Engineering已经编写了一个脚本来自动化这个过程。

正常操作（自动）
================

#. 在本地系统上（而不是在承载基础设施的系统上），请确保安装了以下软件包：
   * python-bugzilla
   * python-configobj
   * python-fedora

#. 运行 "bugzilla login" 并成功接收授权cookie。

#. 克隆 the fedora-infrastructure 工具仓库：
    ::

        git clone https://pagure.io/releng.git

#. 在scripts/process-git-requests 中，运行“process-git-requests”。

手动操作
========

为已经存在的一个包创建新分支
----------------------------

#. ssh 连接 ``pkgs.fedoraproject.org``

#. ``pkgdb-client edit -u $YOURUSERNAME -b $NEWBRANCH --master=devel $NAMEOFPACKAGE``

#. ``pkgdb2branch.py $NAMEOFPACKAGE``
