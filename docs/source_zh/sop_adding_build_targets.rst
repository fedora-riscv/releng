.. SPDX-License-Identifier:    CC-BY-SA-3.0


============
添加构建目标
============

说明
====
每一个新版本，我们都会为下一个版本创建一个构建目标。本SOP将描述准备新构建目标所需的步骤。

操作
====
添加生成目标是一项复杂的任务。它包括更新koji、git和fedora发布包。

.. _adding_build_targets_koji:

Koji
----
在Koji中，需要制作几个收集标签，并创建一个目标将它们联系在一起。我们创建了一个以发行版命名的基本集合标记，以及一个构建标记，
用于保存我们在buildroots中使用的一些不属于发行版的东西（glibc32/glibc64）。对上一版本的继承用于所有权和包数据，以及buildroots内容数据。

使用 ``add-tag`` 、 ``add-tag-inheritance`` 、 ``edit-tag`` 、 ``add-target`` 命令。

::

    $ koji add-tag --help
    Usage: koji add-tag [options]  name
    (Specify the --help global option for a list of other help options)

    Options:
    -h, --help       show this help message and exit
    --parent=PARENT  Specify parent
    --arches=ARCHES  Specify arches


    $ koji add-tag-inheritance --help
    Usage: koji add-tag-inheritance [options]  tag parent-tag
    (Specify the --help global option for a list of other help options)

    Options:
    -h, --help            show this help message and exit
    --priority=PRIORITY   Specify priority
    --maxdepth=MAXDEPTH   Specify max depth
    --intransitive        Set intransitive
    --noconfig            Set to packages only
    --pkg-filter=PKG_FILTER
    Specify the package filter
    --force=FORCE         Force adding a parent to a tag that already has that
    parent tag

    $ koji edit-tag --help
    Usage: koji edit-tag [options] name
    (Specify the --help global option for a list of other help options)

    Options:
      -h, --help       show this help message and exit
      --arches=ARCHES  Specify arches
      --perm=PERM      Specify permission requirement
      --no-perm        Remove permission requirement
      --lock           Lock the tag
      --unlock         Unlock the tag
      --rename=RENAME  Rename the tag

    $ koji add-target --help
    Usage: koji add-target name build-tag <dest-tag>
    (Specify the --help global option for a list of other help options)

    Options:
    -h, --help  show this help message and exit

例如，如果我们想创建Fedora 17标签，我们会执行以下操作：

::

    koji add-tag --parent f16-updates f17
    koji add-tag --parent f17 f17-updates
    koji add-tag --parent f17-updates f17-candidate
    koji add-tag --parent f17-updates f17-updates-testing
    koji add-tag --parent f17-updates-testing f17-updates-testing-pending
    koji add-tag --parent f17-updates f17-updates-pending
    koji add-tag --parent f17-updates f17-override
    koji add-tag --parent f17-override --arches=i686,x86_64 f17-build
    koji add-tag-inheritance --priority 1 f17-build f16-build
    koji edit-tag --perm=fedora-override f17-override
    koji edit-tag --lock f17-updates
    koji add-target f17 f17-build

.. note::
    `Bodhi`_ and `Taskotron`_ 使用 ``-pending`` 标签来跟踪和测试提议的更新。这些标签不是构建目标，也不会被制作成repo，所以合适的继承并不重要。

Git
---

托管在Fedora Infrastructure  ansible中的pkgdb_sync_git_branches.py文件（roles/distgit/templates/pkgdb_sync_git_blanches.py）需要针对新目标进行更新，以进行分支。

使用新的分支信息更新 ``BRANCHES`` ，分支名称映射到作为其父分支的分支。

::

    BRANCHES = {'el4': 'rawhide', 'el5': 'rawhide', 'el6': 'f12',
            'OLPC-2': 'f7',
            'rawhide': None,
            'fc6': 'rawhide',
            'f7': 'rawhide',
            'f8': 'rawhide',
            'f9': 'rawhide',
            'f10': 'rawhide',
            'f11': 'rawhide',
            'f12': 'rawhide',
            'f13': 'rawhide', 'f14': 'rawhide'}


并使用从pkgdb分支字符串到git分支字符串的转换来更新 ``GITBRANCHES`` ：

::

    GITBRANCHES = {'EL-4': 'el4', 'EL-5': 'el5', 'EL-6': 'el6', 'OLPC-2': 'olpc2',
                   'FC-6': 'fc6', 'F-7': 'f7', 'F-8': 'f8', 'F-9': 'f9', 'F-10': 'f10',
                   'F-11': 'f11', 'F-12': 'f12', 'F-13': 'f13', 'F-14': 'f14', 'devel': 'rawhide'}


还需要为活动分支更新genacls.pkgdb文件，以便为生成ACL。更新 ``ACTIVE`` 变量。genacls.pkgdb位于puppet中（modules/gitolite/files/distgit/genacls.pkgdb）。
格式为pkgdb分支字符串到git分支字符串（直到pkgdb使用git分支串为止）：

::

    ACTIVE = {'OLPC-2': 'olpc2/', 'EL-4': 'el4/', 'EL-5': 'el5/',
              'EL-6': 'el6/', 'F-11': 'f11/', 'F-12': 'f12/', 'F-13': 'f13/',
              'F-14': 'f14/', 'devel': 'rawhide'}

fedora-release
--------------
目前，fedora发布包提供了在构建包时使用的 ``%{?dist}`` 定义。创建新目标时，必须为具有新dist定义的集合构建fedora版本。

Comps
-----
* 在Fedora Hosted git (ssh://git.fedorarhosted.org/git/comps.git)中的comps模块中，基于上一版本创建并添加一个新的comps文件。（只需复制即可。）将新文件添加到 ``po/POTFILES.in`` 。
* 当rawhide在koji中重定目标以指向新版本时，将 ``Makefile`` 更新为新版本的目标comps-rawhide.xml。
* 提交后不要忘记 ``git push`` 您的更改。

验证
====
考虑到创建新的构建目标所需的所有更改的复杂性，验证的最佳方法是尝试构建。考虑到fedora版本必须先于其他版本构建，以便dist标签能够正确翻译，这是一个很好的测试用例。例如，这被用来测试新的Fedora 15目标：

* 使用pkgdb请求发布软顶帽的F-15分支
* 使用pkgdb2branch.py实际创建分支
* 更新fedora版本克隆
* 为新的dist定义调整rawhide中的.spec文件
* commit/build
* 跟踪koji构建以确保使用正确的标记

如果 ``fedora-release`` 在发布时不使用dist，那么它不会测试dist。通过第二个使用dist的包进行验证是个好主意。

.. _Bodhi: https://fedoraproject.org/wiki/Bodhi
.. _Taskotron: https://fedoraproject.org/wiki/Taskotron
