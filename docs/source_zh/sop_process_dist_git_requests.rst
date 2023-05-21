.. SPDX-License-Identifier:    CC-BY-SA-3.0

===================================
处理 fedora-scm-requests 工单
===================================

说明
===========

当打包者想要将新软件包添加到 Fedora 或新的 dist-git 分支时，他们需要经历新的软件包流程，一旦他们的软件包审核获得批准，他们就会使用 `fedrepo-req` 工具在 `fedora-scm-requests queue
<https://pagure.io/releng/fedora-scm-requests>`_ 队列中提交工单。

定期地，（每天？）发布工程需要使用 `fedrepo-req-admin` 工具审查和处理此队列。

设置
=====

发布工程需要在本地设置多个值，并在许多服务器端系统中具有足够的权限。

#. pagure.io 令牌。请参阅 fedrepo-req README 有关从何处获取此内容的说明。
#. src.fedoraproject.org 由 `pagure-admin` 生成的令牌。询问 @pingou 如何获得。
   如果自己执行此操作，请转到 pkgs01 并运行
   `PAGURE_CONFIG=/etc/pagure/pagure.cfg pagure-admin admin-token create -h`
   以获取更多信息。
#. pdc 令牌。请参阅 PDC SOP 以获取其中之一。

操作
======

#. 运行 `fedrepo-req-admin list` 以列出所有开放的请求。
#. 运行 `fedrepo-req-admin process N` 来处理特定工单。
#. 运行 `fedrepo-req-admin processall` 所有以遍历所有工单。
