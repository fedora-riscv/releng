.. SPDX-License-Identifier:    CC-BY-SA-3.0

=============================================
Fedora 发布工程贡献指南
=============================================

Fedora Release Engineering 使用许多不同的实用程序，这些实用程序在相应的上游位置得到维护。
Fedora Release Engineering 实施“上游优先”的政策，如果实用程序存在错误或需要的功能，我们会
在考虑使用 Fedora 特定补丁之前，优先考虑解决上游问题。

Fedora Release Engineering 还有许多严格针对 Fedora 的脚本和实用程序，以自动化与 Fedora 本身
相关的任务和流程，并包含在托管在 `Pagure`_ 上的 `releng git repository`_ 中。如果您想要为此存储库做出贡献，请
参考 :ref:`contributing-to-releng` 部分。

.. _contributing-to-releng:

为 releng 贡献
======================

如果要为 releng `git`_ 存储库做出贡献（其中包含这些文档的源 reStructured Text 版本），您首先
需要拥有 `Fedora Account System`_ (FAS) 帐户，登录 `pagure.io`_ ，然后 fork `releng git repository`_ 。

一旦您 fork 了 `releng git repository`_ ，您需要设置远程上游 git 克隆以跟踪官方 releng 存储库。虽
然不是强制性的，但通常将远程上游称为 ``upstream`` ，可以使用以下命令在本地 git clone 所在的目录中
执行此操作：


.. code:: bash

    $ git remote add upstream https://pagure.io/releng.git

.. note::

    如果你目前还不熟悉 git，强烈建议你访问 git 的upstream并熟悉一下。

    http://www.git-scm.com/


RelEng 开发者工作流程
-------------------------

对于开发者工作流程，有许多选项，但 Fedora releng 存储库推荐的工作流程是基于 git 术语中的“ `Topic Branch`_ ”的工作流程。
这是 Fedora Release Engineering 贡献者可以提交代码和文档更改到 `releng git repository`_ 的方式。

常规工作流程如下：

* Checkout 克隆到本地的 releng repository 的 ``main`` 分支。

  ::

    $ git checkout main

* 拉取upstream并合并到本地主分支，以确保您的主分支与上游的最新更改保持一致。然后将其推送到您的克隆，以便origin知道更改。

  ::

    $ git pull --rebase upstream main
    $ git push origin main

* 从main创建主题分支。

  ::

    $ git checkout -b my-topic-branch

* 在主题分支中进行更改，并将其提交到主题分支。

  ::

    $ vim somefile.py

    .... make some change ...

    $ git add somefile.py
    $ git commit -s -m "awesome patch to somefile.py"

* 此步骤是可选的，但建议使用，以避免在upstream提交时发生冲突。在这里，我们将再次Checkout main 并合并
  ``upstream/main`` ，以便我们可以在本地解决任何冲突。

  ::

    $ git checkout main
    $ git pull --rebase upstream main
    $ git push origin main

* 在提交pull request之前在main上rebase

  ::

    $ git rebase main

    ..... Resolve any conflicts if needed ......

* 将您的主题分支推送到您的fork在 pagure 中的origin。

  ::

    $ git push origin my-topic-branch


* 在 Rel Eng Pagure 上开启一个 pull request。 https://pagure.io/releng/pull-requests



开发人员工作流程提示和技巧
----------------------------------

以下是一些 Fedora 发布工程开发人员工作流程提示和技巧，由团队的当前成员使用，以帮助协助开发。

pull upstream
^^^^^^^^^^^^^^^


下面是一个有用的 shell 函数，可以放在 ``~/.bashrc`` 中，以帮助自动化开发人员工作流的某些方面。它将允许您将 upstream main 分支或开发分支合并到您 fork 的存储库中，以便轻松与 upstream 存储库保持一致。

以下是要添加到 ``~/.bashrc`` 中的 bash 函数，并确保在添加后使用 ``source ~/.bashrc`` 以“启用”该功能。

::

    pullupstream () {
        if [[ -z "$1" ]]; then
            printf "Error: must specify a branch name (e.g. - main, devel)\n"
        else
            pullup_startbranch=$(git describe --contains --all HEAD)
            git checkout $1
            git pull --rebase upstream $1
            git push origin $1
            git checkout ${pullup_startbranch}
        fi
    }

有了这个功能，你也可以轻松地拉取和合并releng主分支，即使使用主题分支，如下所示：

::

    $ git status
    On branch docs
    nothing to commit, working directory clean

    $ pullupstream main
    Switched to branch 'main'
    Your branch is up-to-date with 'origin/main'.
    Already up-to-date.
    Everything up-to-date
    Switched to branch 'docs'

    $ git status
    On branch docs
    nothing to commit, working directory clean

现在，您回到了主题分支，您可以轻松地在本地主分支上重新定位，以解决干净拉取请求提交时可能出现的任何合并冲突。

::

    $ git rebase main
    Current branch docs is up to date.


RelEng Upstream 工具
=====================

Fedora发布工程团队使用许多存在于其自己的上游项目空间中的工具。这些是每个Fedora发布工程师都应该熟悉的工具，如果存在错误或需要功能，我们应该首先参与到相应的上游项目中解决问题，然后再考虑携带Fedora特定的补丁。

工具列表
----------

工具发布工程积极参与 upstream
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

以下是一组工具，它们是发布工程团队和我们的流程的核心。我们积极参与这些项目的 upstream。对于这些工具，我们建议使用与此git存储库概述相同的git贡献工作流程。

* `koji <https://pagure.io/koji>`_ -
  Fedora 使用的构建系统
* `mash <https://pagure.io/mash>`_ -
  从 koji 标签创建存储库的工具，并解决多库依赖项。
* `pungi <https://pagure.io/pungi>`_ -
  Fedora 组合工具
* `Product Defintion Center (PDC)
  <https://github.com/release-engineering/product-definition-center>`_ -
  用于存储和查询产品元数据的存储库和 API
* `koji-containerbuild
  <https://github.com/release-engineering/koji-containerbuild>`_ -
  Koji 插件，用于将 OSBS 与 Koji 集成

工具发布工程是最活跃的客户
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

以下是 Release Engineering 团队直接使用或作为 Release Engineering 基础设施中其他工具的副作用所使用的一组工具。
这些工具在需要 Bug 修复或增强功能时应始终从上游中调用，但它们不是 Release Engineering 团队在其持续上游开发方面非
常活跃的工具，并将推迟到每个上游的推荐贡献工作流程。

* `fedpkg <https://pagure.io/fedpkg>`_ -
  Fedora（和EPEL）开发人员的命令行实用程序。它与dist-git，koji，rpmbuild，git等交互。
* `rpkg <https://pagure.io/rpkg>`_ -
  用于在 git 源代码控制中处理 rpm 打包的库（由 Fedpkg 使用）
* `dist-git <https://github.com/release-engineering/dist-git>`_ -
  专门设计用于保存 RPM 包源的远程 Git 存储库。
* `creatrepo <http://createrepo.baseurl.org/>`_ -
  一个从一组rpm文件生成repodata的python程序。
* `createrepo_c <https://github.com/rpm-software-management/createrepo_c>`_ -
  创建存储库的C实现
* `oz <https://github.com/clalancette/oz>`_ -
  用于自动安装操作系统的程序和类集。
* `imagefactory <http://imgfac.org/>`_ -
  imagefactory 为各种操作系统/云组合构建映像。
* `sigul <https://pagure.io/sigul>`_ -
  自动GPG签名系统
* `mock <https://github.com/rpm-software-management/mock/wiki>`_ -
   用于在prestine buildroots中构建软件包的工具
* `fedmsg <http://www.fedmsg.com/en/latest/>`_ -
  Fedora 基础设施消息总线
* `lorax <https://github.com/rhinstaller/lorax>`_ -
  构建安装树和映像的工具
* `OpenShift <http://www.openshift.org/>`_ -
  红帽的开源平台即服务
* `OSBS <https://github.com/projectatomic/osbs-client>`_ -
  一组实用程序，可将 OpenShift 转换为分层映像构建系统
* `taskotron <https://fedoraproject.org/wiki/Taskotron>`_ -
  用于自动执行任务的框架。
* `pulp <http://www.pulpproject.org/>`_ -
  一个用于管理内容存储库（如软件包）并将内容推送给大量客户的平台
* `crane <https://github.com/pulp/crane>`_ -
  Crane 是一个小型只读 Web 应用程序，它提供了足够的 docker 注册表 API 来支持“docker pull”
* `pagure <https://pagure.io/pagure>`_
  以 git 为中心的 forge
* `rpm-ostree <https://github.com/projectatomic/rpm-ostree>`_ -
  将 RPM 存储在 OSTree 存储库中，并从 commit 进行原子升级
* `ostree <https://wiki.gnome.org/Projects/OSTree>`_ -
  用于管理可引导、不可变、版本化的文件系统树的工具。

.. _releng git repository: https://pagure.io/releng
.. _Pagure: https://pagure.io/pagure
.. _Fedora Account System: https://admin.fedoraproject.org/accounts
.. _pagure.io: https://pagure.io
.. _Topic Branch: http://www.git-scm.com/book/en/v2/Git-Branching-Branching-Workflows#Topic-Branches
.. _git: http://www.git-scm.com
