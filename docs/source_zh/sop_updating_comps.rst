.. SPDX-License-Identifier:    CC-BY-SA-3.0


==============
更新 Comps
==============

说明
===========
当我们开始一个新的 Fedora 开发周期时（当我们切换 rawhide 分支时），我们必须为新版本创建一个新的 comps 文件。本 SOP 涵盖该操作。

操作
======

#. 克隆 comps repo

   ::

        $ git clone ssh://git@pagure.io/fedora-comps.git

#. 为下一版本创建新的 comps 文件：

   ::

        $ cp comps-f24.xml.in comps-f25.xml.in

#. 编辑 Makefile 以更新 comps-rawhide 目标

   ::

        - -comps-rawhide: comps-f24.xml
        - -       @mv comps-f24.xml comps-rawhide.xml
        +comps-rawhide: comps-f25.xml
        +       @mv comps-f25.xml comps-rawhide.xml

#. 将新的 comps 文件添加到源代码管理：

   ::

        $ git add comps-f25.xml.in

#. 在 po/POTFILES.in 中编辑已翻译的合成文件列表，以反映当前支持的版本。

   ::

        -comps-f22.xml
        +comps-f25.xml

#. 推送：

   ::
        $ git push

验证
============
在此更改后，可以查看 rawhide compose 的日志，以确保使用了正确的 comps 文件。

运行之前考虑
=======================
目前尚无。
