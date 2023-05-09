.. SPDX-License-Identifier:    CC-BY-SA-3.0

==================
清理AMIs过程
==================

说明
===========

Fedora AMI每天都会上传到亚马逊网络服务。随着时间的推移，AMI的数量不断增加，必须手动移除。手动删除会带来一系列问题，其中错过删除AMI是一个可能出现的问题。

脚本的目标是使过程自动化，并继续定期删除AMI。脚本的报告被推送到 `Pagure repo`_ 。

操作
======

`Fedora RelEng repo`_ 中的 ``scripts`` 目录下有一个名为 ``clean-amis.py`` 的脚本。

该脚本在Fedora基础设施中作为定时作业运行，以删除旧的AMI。所选AMI的权限将更改为私有权限。这是为了确保如果社区中有人提出问题，我们可以选择将AMI重新公开。10天后，如果没有提出任何投诉，AMI将被永久删除。

整个过程可以分为几个部分：

- 从datagrepper获取数据。基于 `--days` 参数，脚本开始从datagrepper获取指定时间段的fedmsg消息，即持续n天，其中n是 `--days` 参数的值。查询的fedmsg主题 `fedimg.image.upload`。

- AMI的选择：在从datagrepper解析AMI之后。对AMI进行过滤，以去除Beta、Two-week Atomic Host和GA发布的AMI。 `compose_type` 设置为 `nightly` 的compose将被选中以进行删除。
  在 `compose label` 中包含日期的compose也会被选中以进行删除。
  GA composes还将compose_type设置为production。因此，为了区分，如果compose_label中有日期，我们会对它们进行过滤。GAcomposes没有日期，而他们有X.Y格式的版本号。

- 更新AMI的权限。选定AMI的权限更改为私有权限。

- 删除AMI。
  10天后，将删除私有AMI。

为了更改AMI的权限，请使用下面给出的命令，添加
`--dry-run` 参数以测试该命令是否有效。添加 `--dry-run` 参数将把AMI打印到控制台。

::

   AWS_ACCESS_KEY={{ ec2_image_delete_access_key_id }} AWS_SECRET_ACCESS_KEY={{ ec2_image_delete_access_key }} PAGURE_ACCESS_TOKEN={{ ami_purge_report_api_key }} ./clean-amis.py --change-perms --days 7 --permswaitperiod 5


为了删除其启动权限已被删除的AMI，请添加
`--dry-run` 参数以测试命令是否有效。添加 `--dry-run` 参数将把AMI打印到控制台。

::

   AWS_ACCESS_KEY={{ ec2_image_delete_access_key_id }} AWS_SECRET_ACCESS_KEY={{ ec2_image_delete_access_key }} PAGURE_ACCESS_TOKEN={{ ami_purge_report_api_key }} ./clean-amis.py --delete --days 17 --deletewaitperiod 10


.. _Pagure repo: https://pagure.io/ami-purge-report
.. _Fedora RelEng repo: https://pagure.io/releng
