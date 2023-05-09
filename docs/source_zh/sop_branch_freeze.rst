.. SPDX-License-Identifier:    CC-BY-SA-3.0


========
分支冻结
========


简介/背景
=========

当下一个版本从rawhide分支出来时，它最初的合成非常像rawhide，每晚合成并且没有更新过程。

一旦Bodhi被激活，我们将向分支推送更新，夜间的组成将开始有所不同。但在Beta或GA预定发布的两周前，我们将开始冻结该版本并停止推送更新。

* 将公告发送到devel-announce邮件列表，注意alpha更改冻结将至少提前一天发生。

.. note::
    对于更新推送者：
        在“更改冻结”中，只有修复已接受的阻止程序或“冻结中断”错误的更新才允许进入主树。请与QA协调任何稳定的更新推送。否则，仅推送到updates-testing。

.. note::
    对于同样Final/GA发布：
        在最终冻结期间，我们不想阻止koji中的任何包，因为这会影响RC的组成。因此，请更新 block_retired.py_ 脚本并删除分支版本引用。

.. _block_retired.py: https://pagure.io/releng/blob/master/f/scripts/block_retired.py
