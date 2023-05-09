.. SPDX-License-Identifier:    CC-BY-SA-3.0


================
添加侧边构建标签
================

定义
====
更大的功能可能需要一段时间才能稳定和落地，或者需要大量的软件包来相互构建，这最容易通过为开发工作提供单独的构建标签来实现。本SOP将描述准备新构建目标所需的步骤。

操作
====
工程师们应该意识到，添加侧边构建目标会在koji中产生额外的newRepo任务。

研究标签
--------

#. 验证标签是否已经存在。

   典型的标签格式是 *PRODUCT*-*DESCRIPTOR* 。 *DESCRIPTOR* 应该是一些简短的内容，清楚地显示标签存在的原因。

   .. note::

      不要太在意什么是一个好的描述符。XFCE 4.8版本侧边构建目标的描述符是 *xfce48* 。KDE通常只是简单地使用 *kde* 作为描述符。做出最佳判断，如果有疑问，请在 ``#fedora-releng`` 的IRC中提问。

   .. admonition:: EPEL6

      ::

         $ koji taginfo epel6-kde

   .. admonition:: EPEL7

      ::

         $ koji taginfo epel7-kde

   .. admonition:: Fedora

      ::

         $ koji taginfo f28-kde

   .. note::
      如果标签已经存在，则通过追加 ``-2`` 并将数字递增一来继续搜索可用标签，直到找到可用标签为止。例如，如果 ``f28-kde`` 已经存在，则搜索 ``f28-kde-2`` 、 ``f28-kde-3`` 等，直到找到合适的标签。

#. 确定合适的体系结构。

   .. admonition:: EPEL6

      ::

         $ koji taginfo dist-6E-epel-build

   .. admonition:: EPEL7

      ::

         $ koji taginfo epel7-build

   .. admonition:: Fedora

      ::

         $ koji taginfo f28-build

创建侧边构建目标
----------------

#. 创建正确的标签

   请注意，语法略有不同，这取决于哪种产品需要侧边构建目标和基于前一步信息的逗号分隔的体系结构列表。


   .. admonition:: EPEL6

      ::

         $ koji add-tag epel6-kde --parent=dist-6E-epel-build --arches=i686,x86_64,ppc64

   .. admonition:: EPEL7

      ::

         $ koji add-tag epel7-kde --parent=epel7-build --arches=aarch64,x86_64,ppc64,ppc64le

   .. admonition:: Fedora

      ::

         $ koji add-tag f28-kde --parent=f28-build --arches=armv7hl,i686,x86_64,aarch64,ppc64,ppc64le,s390x

#. 创建目标

   .. admonition:: EPEL6

      ::

         $ koji add-target epel6-kde epel6-kde

   .. admonition:: EPEL7

      ::

         $ koji add-target epel7-kde epel7-kde

   .. admonition:: Fedora

      ::

         $ koji add-target f28-kde f28-kde

#. 查找与新创建的目标相关联的newRepo任务的taskID

   ::

      $ koji list-tasks --method=newRepo
      ID       Pri  Owner                State    Arch       Name
      25101143 15   kojira               OPEN     noarch     newRepo (f28-kde)


#. 确保newRepo任务正在所有体系结构中运行

   ::

      $ koji watch-task 25101143
      Watching tasks (this may be safely interrupted)...
      25101143 newRepo (f28-kde): open (buildvm-14.phx2.fedoraproject.org)
      25101154 createrepo (i386): closed
      25101150 createrepo (ppc64le): closed
      25101152 createrepo (ppc64): closed
      25101151 createrepo (aarch64): closed
      25101149 createrepo (armhfp): closed
      25101153 createrepo (s390x): open (buildvm-ppc64le-04.ppc.fedoraproject.org)
      25101148 createrepo (x86_64): open (buildvm-aarch64-21.arm.fedoraproject.org)
      

#. 请求新标签的包自动签名

   在 `pagure基础设施`_ 中提交一个票据请求为软件包自动签名启用新标签。

#. 更新Pagure发布

   根据以下模板更新发布，该模板假设在Fedora 28下为KDE创建了一个侧边目标。 *TAG_NAME* 已创建：

      $ koji add-tag f28-kde --parent=f28-build --arches=armv7hl,i686,x86_64,aarch64,ppc64,ppc64le,s390x

      $ koji add-target f28-kde f28-kde

      您可以使用以下内容进行构建：
      
      $ fedpkg build --target=f28-kde

      完成后请告知我们，我们将把所有构建转移到f28中。


清理
====
Fedora Release Engineering负责将侧边构建目标和标签中的包合并回主标签中。申请者将在准备好进行以下程序时更新原始票证。

#. 移除目标

   ::

      $ koji remove-target <SIDE_TAG_NAME>

#. 合并侧边构建至主目标

   从 `Fedora Release Engineering Repository`_ 获取最新的checkout并从脚本目录运行 `mass-tag.py` 。

   ::

      $ ./mass-tag.py --source <SIDE_TAG_NAME> --target <MAIN_TAG_NAME> > mass_tag.txt

   .. note::
      Fedora的 *MAIN_TAG_NAME* 通常是挂起的子标签，例如当bodhi不管理更新时的 ``f28-pending`` 。启用bodhi并管理更新之后合并到 ``f28-updates-candidate`` 中。

#. 将输出粘贴到原始票证中

   将mass-tag.py的输出粘贴到pagure/reling票证中，以显示哪些包被合并，以及哪些包需要为那些在buildroot上工作的人重建。

标签 **永远** 不会被删除。

运行之前请考虑
==============

* 要做的工作量是否值得newRepo任务的成本。
* 如果只有少量的包，重写可能会更好。
* 是否正在进行大规模重建？大规模重建过程中不允许使用侧边标签

.. _pagure基础设施: https://pagure.io/fedora-infrastructure/issues
.. _Fedora Release Engineering Repository: https://pagure.io/releng/
