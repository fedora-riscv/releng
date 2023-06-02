.. SPDX-License-Identifier:    CC-BY-SA-3.0


==================
Sigul 客户端设置
==================

本文档介绍如何配置 sigul 客户端。有关 sigul 的更多信息，请参阅 `User:Mitr <User-Mitr>`_

先决条件
=============


#. 安装 ``sigul`` 及其依赖项。它在Fedora和EPEL中都可用：

   在 Fedora 上:

   ::

        dnf install sigul

   在 RHEL/CentOS 上(使用 EPEL):

   ::

        yum install sigul

#. 确保您的 koji 证书和
   `Fedora CA 证书 <Fedora-Cert>`_ 存在于您运行 sigul 客户端系统的以下位置上：

   * ``~/.fedora.cert``
   * ``~/.fedora-server-ca.cert``
   * ``~/.fedora-upload-ca.cert``

#. 编写签名需要 koji 的管理员权限。

配置
=============

#. 运行 ``sigul_setup_client``
#. 为 NSS 数据库选择一个密码。默认情况下，这将存储在磁盘上的 ``~/.sigul/client.conf`` 中。
#. 选择导出密码。您只需要记住它，直到完成
   ``sigul_setup_client``.
#. 输入您之前选择的数据库密码，然后输入导出密码。应会看到消息 ``pk12util: PKCS12 IMPORT SUCCESSFUL``
#. 再次输入数据库密码。您应该会看到消息 ``Done``.
#. 假设您在 phx2 中运行 sigul 客户端，请编辑
   ``~/.sigul/client.conf`` 以包含以下行：

::

    [client]
    bridge-hostname: sign-bridge.phx2.fedoraproject.org
    server-hostname: sign-vault.phx2.fedoraproject.org

更新您的 Fedora 证书 
================================

当您的 Fedora 证书过期时，更新证书并运行以下命令：

::

    $ certutil -d ~/.sigul -D -n sigul-client-cert
    $ sigul_setup_client

.. _User-Mitr: https://fedoraproject.org/wiki/User:Mitr
.. _Fedora-Cert: https://fedoraproject.org/wiki/Package_maintenance_guide#Installing_fedpkg_and_doing_initial_setup
