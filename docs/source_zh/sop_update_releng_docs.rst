.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
更新 RelEng 渲染的文档
===========================

说明
===========
.. Put a description of the task here.

当Release Engineering文档在 `RelEng git repository`_ 的 ``docs/source`` 中使用 `Sphinx`_ `reStructured Text`_
源代码进行改进并遵循了 :doc:`贡献 <contributing>` 之后，必须有人手动执行一个过程，以便更新托管在 `Fedora RelEng docs`_
的 `pagure`_ 文档空间中的文档。

操作
======
.. Describe the action and provide examples

为了使用 `Sphinx`_ 渲染文档，您需要首先确保已安装软件包：

::

    $ dnf install python-sphinx

然后我们需要克隆 RelEng repository 和 RelEng docs repository
（docs git 仓库由 pagure 自动提供）。
`releng` repository 中有一个脚本，负责为我们干净地更新文档站点。


::

    $ ./scripts/update-docs.sh

该文档现已上线。

.. note::
    这将需要具有权限的人员推送到 releng repository 的 rawhide 分支。如果您好奇谁都有这种能力，请参阅
    :doc:`Main Page <index>` 并联系 “Team
    Composition”

验证
============
.. Provide a method to verify that the action completed as expected (success)

访问 `Fedora RelEng docs`_ 网站并验证更改是否实时反映在文档站点上。

运行之前考虑
=======================
.. Create a list of things to keep in mind when performing action.

目前没有需要考虑的内容。docs git 存储库只是一个静态的 html 托管空间，我们可以重新渲染文档并在必要时再次推送到它。

.. _Sphinx: http://sphinx-doc.org/
.. _reStructured Text: https://en.wikipedia.org/wiki/ReStructuredText
.. _RelEng git repository: https://pagure.io/releng
.. _pagure: https://pagure.io/pagure
.. _Fedora RelEng docs: https://docs.pagure.org/releng/
