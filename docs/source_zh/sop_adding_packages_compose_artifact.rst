.. SPDX-License-Identifier:    CC-BY-SA-3.0


========================
将软件包添加到发布工件中
========================

说明
====
如果Fedora贡献者希望将一个软件包添加到计划发布的Compose工件（如安装程序ISO映像、liveCD、云镜像、Vagrant、Docker等）中，由于发行版之间不同组件的相互依赖性，必须遵循以下过程。

背景
----
首先，提供一些信息，说明这一切是从哪里来的，以及是如何结合在一起的。

有一个“安装树”的概念，它是安装时可用的软件包的集合。这是整个Fedora软件包集合的一个庞大子集，也是终端用户选择从 `Anaconda`_ 安装程序中自定义安装时可以使用的最可能的软件包池。
它也是 `fedora-kickstarts`_ 用于通过 `pungi`_ 生产compose的各种组件然后生成发布工件的kickstart文件可以使用的最可能的软件包池。

安装树本身是由 `comps`_ 组定义的，因此为了将一个全新的软件包添加到其中一个发布工件中，必须将该包放置在适当的 `comps`_ xml文件中。有关“适当的 `comps`_ _xml文件”的具体定义以及添加新包可能需要什么样的批准或审查的更多信息，请参阅 `本指南`_ 。

操作
====

我们需要编辑特定于我们的目标Fedora版本的comps文件。例如，如果我们以Fedora 25为目标，我们将编辑 `comps`_ git仓库中的 ``comps-f25.xml.in`` ，这应该根据 `如何编辑comps过程`_ 进行修改。

如果添加的包是预先存在的comps组的一部分，该comps组已经在目标发布工件的 `fedora-kickstarts`_ kickstart文件中使用，那么我们就完成了。

然而，如果添加了一个新的comps组，那么我们需要在相应的 `fedora-kickstarts`_ kickstart文件中包含这一新的comp组，类似于下面的文件。

::

    %packages
    @mynewcompsgroup


接下来，我们需要告诉 `pungi`_ Variants关于新组的数据以及它与相应 `Variant`_ 的关系。这些信息保存在 `Fedora Pungi Configs`_ `pagure`_ git forge仓库中。需要编辑的文件是 ``variants-fedora.xml`` ，可以在 `web浏览器`_ 中查看。

这些都完成就可以了。

验证
====

请验证下一个compose是否成功以及所做的更改是否没有导致任何问题。这可以从 `Fedora Product Definition Center`_ 完成，该中心是关于Composes及其生成工件的信息的中央存储区。

运行之前请考虑
==============
.. Create a list of things to keep in mind when performing action.

.. _pagure: https://pagure.io/
.. _pungi: https://pagure.io/pungi
.. _comps: https://pagure.io/fedora-comps
.. _Anaconda: https://fedoraproject.org/wiki/Anaconda
.. _Fedora Pungi Configs: https://pagure.io/pungi-fedora
.. _fedora-kickstarts: https://pagure.io/fedora-kickstarts
.. _web浏览器: https://pagure.io/pungi-fedora/blob/master/f/variants-fedora.xml
.. _Fedora Product Definition Center: https://pdc.fedoraproject.org/compose/
.. _本指南:
    https://fedoraproject.org/wiki/How_to_use_and_edit_comps.xml_for_package_groups
.. _Variant:
    https://sgallagh.wordpress.com/2016/03/18/sausage-factory-multiple-edition-handling-in-fedora/
.. _如何编辑comps过程:
    https://fedoraproject.org/wiki/How_to_use_and_edit_comps.xml_for_package_groups#How_to_edit_comps
