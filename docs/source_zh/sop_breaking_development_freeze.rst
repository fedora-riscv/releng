.. SPDX-License-Identifier:    CC-BY-SA-3.0


============
中断开发冻结
============

``FIXME: 需要解决怎样到达FEDORA-VERSION-NEXT``

说明
====
需要例外才能冻结策略的包必须通过本SOP运行。

为以下重要发布里程碑设置了以下冻结策略：

* `String Freeze`_
* `Beta Freeze`_
* `Final Freeze`_

请参阅 `Fedora Release Life Cycle`_ 获取所有冻结、日期和异常处理的概览，或者发布工程[https://fedorapeople.org/groups/schedule/f-{{FedoraVersionNumber|next}}/f-{{FedoraVersionNumber|next}}-releng-tasks.html 当前版本的日历].

操作
====
一旦包被接受，此命令就可以正确地对其进行标记：

::

    $ koji move-pkg --force dist-f{{FedoraVersionNumber|next}}-updates-candidate dist-f{{FedoraVersionNumber|next}} <PKGNAME>
    $ koji tag-pkg --force f{{FedoraVersionNumber|next}}-<RELEASE> <PKGNAME>

其中，<PKGNAME>是软件包名称，<RELEASE>是该软件包应该登陆的第一个版本（例如，alpha、beta、final）。  

验证
====
``koji`` 客户端报告成功或者失败。对于二次验证，运行以下命令：

::

    $ koji latest-pkg dist-f{{FedoraVersionNumber|next}} <PKGNAME>
    $ koji latest-pkg dist-f{{FedoraVersionNumber|next}}-updates-candidate <PKGNAME>

运行之前请考虑
==============
* 变更符合规定的政策（见以上链接）
* 已经根据 `Blocker Bug Process`_ 或 `Freeze Exception Bug Process` 批准变更


.. _Beta Freeze: https://fedoraproject.org/wiki/Milestone_freezes
.. _Final Freeze: https://fedoraproject.org/wiki/Milestone_freezes
.. _String Freeze: https://fedoraproject.org/wiki/Software_String_Freeze_Policy
.. _Fedora Release Life Cycle:
    https://fedoraproject.org/wiki/Fedora_Release_Life_Cycle
.. _Blocker Bug Process:
    https://fedoraproject.org/wiki/QA:SOP_blocker_bug_process
.. _Freeze Exception Bug Process:
    https://fedoraproject.org/wiki/QA:SOP_freeze_exception_bug_process
