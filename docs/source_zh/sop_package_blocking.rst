.. SPDX-License-Identifier:    CC-BY-SA-3.0


================
阻塞软件包
================

说明
===========
如果一个 `软件包从 Fedora 中删除（退休）`_ ，例如因为它被重命名，它需要在 Koji 中被阻塞。这可以防止创建新的软件包构建和发行版RPM构建。软件包在
``tags`` 列表中被阻塞，由于继承，在最旧的标签处阻塞包就足够了，这将使它在上游标签中也不可用。

操作
======
已停用包的阻塞由 `block_retired.py`_ 脚本完成，作为每日 Rawhide 和 Branched 组合的一部分。


.. _软件包从 Fedora 中删除（退休）:
    https://fedoraproject.org/wiki/How_to_remove_a_package_at_end_of_life

.. _block_retired.py:
    https://pagure.io/releng/blob/master/f/scripts/block_retired.py
