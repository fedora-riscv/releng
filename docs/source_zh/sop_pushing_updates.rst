.. SPDX-License-Identifier:    CC-BY-SA-3.0


===============
推送更新
===============

说明
===========

Fedora 更新通常每天推送一次。本标准操作程序涵盖所涉及的步骤。

协调
----------

Releng 轮换谁在何时推送更新。请协调并仅在您期望或已通知其他相关人员您正在这样做时推送更新。请参阅： https://apps.fedoraproject.org/calendar/release-engineering/
查看列表或在 irc 上，您可以使用 zodbot 在任何频道中运行 ``.pushduty`` ，以查看本周谁值班。

登录到计算机以签署更新
--------------------------------

登录到配置为sigul 客户端支持并安装了 bodhi 客户端的计算机。
目前，这台机器是：
``bodhi-backend01.phx2.fedoraproject.org``

决定要推送的版本
------------------------------------------

* 如果正在进行 Freeze ，则不应推送分支版本的所有 stable 请求，而应仅推送 QA
  将在 releng 工单中请求的特定阻塞程序或冻结异常请求。

* 如果没有正在进行的 Freeze ，如果你愿意，你可以同时推送所有的Fedora和EPEL版本。

* 某些分支可能会不时有紧急请求，您只能在被要求时推送这些请求。
  但请注意， bodhi2 会自动推送具有安全更新的分支。

获取要推送的包列表
------------------------------

::

    $ sudo -u apache bodhi-push --releases 'f26,f25,f24,epel-7,EL-6' --username <yourusername>
    <enter your password+2factorauth, then your fas password>

有时您会看到警告“警告： foobar-1.fcxx 具有未签名的版本并且已被跳过”，这意味着这些更新当前正在签名，并且可以通过在 fxx-signing-pending 标签中列出被标记的构建来验证。

::
    $ koji list-tagged fxx-signing-pending

如果您希望对包进行签名，此时可以对推送答复“n”（见下文）。或者，您可以在对包进行签名时在窗口中保持此请求处于打开状态，然后返回并答复 y。

列出上面您希望推送的版本：25 24 5 6 7等

还可以指定 ``--request=testing`` 来限制推送。有效选项为
``testing`` 或 ``stable`` 。

更新列表应位于要推送的每个分支的名为 ``Stable-$Branch``
或 ``Testing-$Branch`` 的缓存目录中。

在冻结期间，您需要执行两个步骤：（例如，Fedora 26 分支被冻结）：

::

    $ sudo -u apache bodhi-push --releases f26 --request=testing \
        --username <username>

然后

::

    $ sudo -u apache bodhi-push --releases 'f25,f24,epel-7,EL-6' --username <username>

在发布候选版本组合阶段，我们会将构建标记为包含在“-compose”标记中（例如f26-compose）。当我们有一个被标记为Gold的候选版本后，我们需要确保所有标记为“-compose”的构建已经被推送到正式版。
一旦我们将所有“-compose”构建都推送到正式版，我们就需要将基本标记（例如f26）克隆到Alpha和Beta里程碑的标记中（例如f26-Alpha）。
在最终发布之后，我们需要锁定基础标记，并在bodhi中调整发布状态，以便更新现在命中“-updates”标记（例如f26-updates）。一旦我们克隆了标记或锁定了标记并在bodhi中进行了调整，我们就可以再次推送稳定更新了。

在冻结期间推送稳定版更新
------------------------------------

在冻结期间，我们需要将包含在组合中的构建发布到稳定版。QA团队会提交一个带有NVR的票据以进行发布推送。

.. note::

    如果您正在推送一个包含多个构建的Bodhi更新，您只需要传递单个构建NVR给bodhi-push，所有其他构建将会被检测并与其一起推送。但是，如果您正在推送多个不相干的Bodhi更新，则每个构建都需要单独列出。

::

    $ sudo -u apache bodhi-push --builds '<nvr1>,<nvr2>,...' --username <username>


没有要推送的更新
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

如果收到消息 ``There are no updates to push.`` 或看到的要推送的稳定版更新请求的包列表与在上述命令的 ``--builds`` 部分中指定的内容相比不正确，则可能发生了以下两种情况之一。

#. 更新还没有达到适当的Karma值

   这应该根据情况而定，如果QA团队已要求将其作为稳定版推出以解决阻止问题，但尚未获得足够的Karma值，则应该与QA团队验证这些更新是否准备好发布，即使没有Karma也可以。
   如果他们准备好了，那么登录Bodhi WebUI，修改更新的Karma阈值为1并添加Karma（如果必要）。这不是我们通常应该做的事情，被认为是一个特殊情况。当更新请求到达RelEng时，它应该具有适当的Karma值。
   有时它没有，只要QA批准，我们就不需要阻塞它。

#. 从未请求过稳定版更新

   稳定版可能没有请求更新，您可以通过在其中一个 bodhi-backend 系统上运行以下命令来解决此问题：

   ::

    bodhi updates request <BODHI-REQUEST-ID> stable



执行 bodhi 推送
----------------------

答复“y”以推动上述命令。

验证
============
#. 用 ``bodhi-monitor-composes`` 监视Bodhi的组合

   ::

    $ sudo -u apache watch -d -n 60 bodhi-monitor-composes

#. 监视系统日志

   ::

    $ sudo journalctl -o short -u fedmsg-hub -l -f

#. 检查流程

   ::

    $ ps axf|grep bodhi

#. 在整个过程中关注 fedmsgs 。它将指示它正在处理的版本等。您可能想在 ``#fedora-fedmsg`` 中观看。

   ::

        bodhi.masher.start -- kevin requested a mash of 48 updates
        bodhi.mashtask.start -- bodhi masher started a push
        bodhi.mashtask.mashing -- bodhi masher started mashing f23-updates
        bodhi.mashtask.mashing -- bodhi masher started mashing f22-updates-testing
        ...
        bodhi.update.complete.stable -- moceap's wondershaper-1.2.1-5.fc23 bodhi update completed push to stable https://admin.fedoraproject.org/updates/FEDORA-2015-13052
        ...
        bodhi.errata.publish -- Fedora 23 Update: wondershaper-1.2.1-5.fc23 https://admin.fedoraproject.org/updates/FEDORA-2015-13052
        bodhi.mashtask.complete -- bodhi masher successfully mashed f23-updates
        bodhi.mashtask.sync.wait -- bodhi masher is waiting for f22-updates-testing to hit the master mirror

#. 搜索特定推送的问题：

   ::

        sudo journalctl --since=yesterday -o short -u fedmsg-hub | grep dist-6E-epel (or f22-updates, etc)

#. 注意：Bodhi 会查看你告诉它推送的东西，看看是否有安全更新，这些分支将首先启动。然后它将触发线程（一次最多 3 个）并完成其余的工作。

运行之前考虑
=======================
推送经常由于标记问题或未签名的包而失败。准备好解决故障并不时重新启动推送

::

    $ sudo -u apache bodhi-push --resume

Bodhi 会问你想继续哪些推送。


推送的常见问题
====================================

* 当推送由于启动进程后添加的新未签名包而失败时。仅使用需要签名的包名称重新运行步骤 4a 或 4b，然后继续。

* 当推送由于没有签名的旧包而失败时，请运行：
  ``koji write-signed-rpm <gpgkeyid> <n-v-r>`` 并恢复。

* 当推送失败时，原因是软件包在移动到稳定版时未被标记为updates-testing： ``koji tag-pkg dist-<tag>-updates-testing <n-v-r>``

* 签名失败时，可能需要要求重新启动 sigul 网桥或服务器。

* 如果更新推送失败并显示：
  ``OSError: [Errno 16] Device or resource busy: '/var/lib/mock/*-x86_64/root/var/tmp/rpm-ostree.*'``
  您需要卸载后端上仍打开的任何 tmpfs 挂载并恢复推送。

* 如果更新推送失败并显示：
  ``"OSError: [Errno 39] Directory not empty: '/mnt/koji/mash/updates/*/../*.repocache/repodata/'``
  则需要在后端重新启动 fedmsg-hub 并恢复。

* 如果更新推送失败，并显示：
  ``IOError: Cannot open /mnt/koji/mash/updates/epel7-160228.1356/../epel7.repocache/repodata/repomd.xml: File /mnt/koji/mash/updates/epel7-160228.1356/../epel7.repocache/repodata/repomd.xml doesn't exists or not a regular file``
  此问题将在 NFSv4中解决，但同时可以通过删除  `.repocache` 目录并恢复推送来解决。
  ``$ sudo rm -fr /mnt/koji/mash/updates/epel7.repocache``

* 如果 Atomic OSTree 组合失败并出现 `Device or Resource busy` 错误，请运行 `mount` 以查看是否有任何杂散的 `tmpfs` 挂载仍处于活动状态：
  ``tmpfs on /var/lib/mock/fedora-22-updates-testing-x86_64/root/var/tmp/rpm-ostree.bylgUq type tmpfs (rw,relatime,seclabel,mode=755)``
  然后，您可以
  ``$ sudo umount /var/lib/mock/fedora-22-updates-testing-x86_64/root/var/tmp/rpm-ostree.bylgUq`` 并恢复推送。

其他问题应由 releng 或 bodhi 开发人员在
``#fedora-releng`` 中解决。


