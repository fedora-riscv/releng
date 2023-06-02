.. SPDX-License-Identifier:    CC-BY-SA-3.0


===============
更新 Critpath
===============

.. note::
    Critpath = "Critical Path，关键路径"

    这是一个被认为对 Fedora “关键”的软件包的集合

说明
===========

PDC 包含有关哪些包是 critpath 的信息，哪些不是。读取 yum repodata（comps 中的 critpath 组和包依赖项）的脚本用于生成此脚本。由于包依赖项会更改，因此应定期更新此列表。

操作
======

#. 在 `releng git repository`_ 中实时发布用于更新 critpath 的工程脚本。

#. 检查 critpath.py 脚本以查看是否需要更新版本列表：

   ::

        for r in ['12', '13', '14', '15', '16', '17']: # 13, 14, ...
            releasepath[r] = 'releases/%s/Everything/$basearch/os/' % r
            updatepath[r] = 'updates/%s/$basearch/' % r

        # Branched Fedora goes here
        branched = '18'

   该 for 循环包含了已经过了最终版本的发布版本号。branched部分包括从Rawhide分支出来但尚未达到最终版本的发行版本（它们在存储库中具有不同的路径，可能没有更新目录，因此它们在单独的部分）。

#. 运行版本的脚本以生成其信息（对于最终版本，这是版本号示例：“17”。对于分支，它是“branched”）。

   ::

        ./critpath.py --srpm -o critpath.txt branched

#. 运行更新脚本以将其添加到 PDC：

   ::

        ./update-critpath --user toshio f18 critpath.txt

   用户名是您的 fas 用户名。您必须在 cvsadmin 中才能更改此设置。分支是 dist-git 分支的名称。critpath.txt 是 critpath.py 的输出进入的文件。该脚本需要一个 PDC 令牌才能与服务器通信，在 /etc/pdc.d/ 中配置。有关更多信息，请参阅 PDC SOP。

.. _releng git repository: https://pagure.io/releng
