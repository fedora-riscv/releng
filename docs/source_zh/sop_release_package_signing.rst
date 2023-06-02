.. SPDX-License-Identifier:    CC-BY-SA-3.0


=======================
发布包签名
=======================

说明
===========
对于 Fedora 的每个公开版本（Alpha、Beta 和 Final），Release Engineering 有责任使用 Fedora 的 GPG 密钥对所有软件包进行签名。这为 Fedora 的用户提供了对 Fedora 提供的软件包的权威性的信心。

:doc:`/sop_create_release_signing_key` 文档解释了创建所用 GPG 密钥的过程。

运行前考虑
=======================

此脚本需要很长时间才能运行，最多需要 4 或 5 天，因此需要在确定要对所有包进行签名之前启动它。

对所有软件包进行签名将导致镜像站点的数据变动较多，因此您需要预计生成以及同步镜像所需的时间会比平常更长，还可能会出现代理服务器问题，因为文件内容改变但文件名仍然相同。

操作
======
#. 使用 ``sigul`` 登录系统并启动 ``screen`` 或 ``tmux`` 会话。
   签名过程需要很长时间 - 如果会话断开连接，screen 允许该过程继续。

   ::

        $ screen -S sign

   或

   ::

        $ tmux new -s sign

#. 请查看发布工程 ``git`` 仓库

   ::
        $ git clone https://pagure.io/releng.git

#. 将目录更改为 ``scripts`` 目录以执行
   ``sigulsign_unsigned.py``.

  例如，要签署 Fedora 13 Alpha 的所有内容，我们将使用：

   ::
        $ ./sigulsign_unsigned.py -vv --tag dist-f13 fedora-13

   这将使用详细输出对软件包进行签名，以便您可以按增量跟踪进度。

验证
============
签名完成后，使用 ``rpmdev-checksig`` 验证包是否已签名。您可以使用最近的 rawhide 组合的输出进行测试。
在这个例子中，我们使用一个已发布的 Fedora 12 软件包：

::

    $ rpmdev-checksig /pub/fedora/linux/releases/12/Everything/i386/os/Packages/pungi-2.0.20-1.fc12.noarch.rpm 
    /pub/fedora/linux/releases/12/Everything/i386/os/Packages/pungi-2.0.20-1.fc12.noarch.rpm: MISSING KEY - 57bbccba

此输出显示 apckage 是使用密钥 ``57bbccba`` 签名的，并且此密钥不存在于本地 rpm 数据库中。如果密钥确实存在于本地 rpm 数据库中，则很可能没有输出，因此最好在没有导入 gpg 密钥的系统上运行它。

