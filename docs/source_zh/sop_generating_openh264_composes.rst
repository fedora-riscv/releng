.. SPDX-License-Identifier:    CC-BY-SA-3.0


============================
生成 Openh264 Composes
============================

说明
===========

Openh264 repos 是一个特例，我们需要以不同的方式为其生成组合。
我们使用 ODCS 生成私有组合， 并将 rpms 发送到思科以在其 CDN 上发布它们。我们这边发布存储库数据。

.. warning:: 我们没有分发这些软件包的所有适当的合法权利，因此我们需要格外小心，以确保它们永远不会通过我们的构建系统或网站分发。

操作
======

需要的权限
------------------

您将需要一些 ODCS 权限才能请求私有组合和来自标签的组合。
您可以在odcs_allowed_clients_users变量的inventory/group_vars/odcs中的 infra/ansible 中进行设置。有关的格式参阅releng用户条目。

获取 odcs 令牌 
------------------

为了生成 odcs 组合，您需要一个 openidc 令牌。

从pagure releng repository运行 ``scripts/odcs/`` 下的 odcs-token.py 生成令牌。

::

    $ ./odcs-token.py

确保RPM包带有正确的签名
-------------------------------------------------------

::

    $ koji write-signed-rpm eb10b464 openh264-2.2.0-1.fc38

其中列出了该分支的密钥，然后是 open264 包和版本。

生成私有 odcs 组合
-------------------------------

使用上面生成的令牌，生成 odcs 私有组合

::

    $ python odcs-private-compose.py <token> <koji_tag> <signingkeyid>

`koji_tag`: fxx-openh264 (Openh264 版本被标记为 fxx-openh264 标签，其中 `xx` 代表 Fedora 版本)

`signingkeyid`: 这个 Fedora 分支的密钥的短哈希。 

这些组合存储在 ``odcs-backend-releng01.iad2.fedoraproject.org`` 上的 ``/srv/odcs/private/`` 目录

将组合拉取到本地计算机
--------------------------------------

我们需要提取 rpms 并 tar 它们以发送到思科。
为此，首先我们需要将组合拉到本地机器上。

在 odcs-backend-releng01.iad2.fedoraproject.org 上将组合迁移到你的主目录
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

由于组合归 `odcs-server` 所有，因此将其拉取到您的主目录

::

    $ mkdir ~/32-openh264
    $ sudo rsync -avhHP /srv/odcs/private/odcs-3835/ ~/32-openh264/
    $ sudo chown -R mohanboddu:mohanboddu ~/32-openh264/

将组合同步到本地计算机
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

请将位于ODCS releng后端的您的主目录中的组合复制到本地机器的临时工作目录中

::

    $ mkdir openh264-20200813
    $ scp -rv odcs-backend-releng01.iad2.fedoraproject.org:/home/fedora/mohanboddu/32-openh264/ openh264-20200813/

进行所需的更改
^^^^^^^^^^^^^^^^^^^^^^^

请按照以下命令制作必要的tar文件以发送到Cisco

::

    $ cd openh264-20200813
    $ mkdir 32-rpms
    # Copy rpms including devel rpms
    $ cp -rv 32-openh264/compose/Temporary/*/*/*/*/*rpm  32-rpms/
    # Copy debuginfo rpms
    $ cp -rv 32-openh264/compose/Temporary/*/*/*/*/*/*rpm 32-rpms/
    # copy the src.rpm
    $ cp -rv 32-openh264/compose/Temporary/*/*/*/*/*src.rpm 32-rpms/
    $ cd 32-rpms
    # Create the tar file with the rpms
    $ tar -cJvf ../fedora-32-openh264-rpms.tar.xz *rpm

我们需要将此 tar 文件以及每个压缩包中的 rpm 列表一起发送给思科。

将组合同步到 sundries01
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

一旦我们从思科获得 rpm 在其 CDN 上更新的确认，请使用 curl 进行验证。例如：

::

    $ curl -I http://ciscobinary.openh264.org/openh264-2.1.1-1.fc32.x86_64.rpm

现在将这些组合推送到 **sundries01.iad2.fedoraproject.org** 和 **mm-backend01.iad2.fedoraproject.org**

在 sundries01 上，我们需要同步到一个由 *apache* 拥有的目录，所以首先我们将其同步到 sundries01 上的主目录。同理，对于 mm-backend01 ，因为该目录归 *root* 所有，我们也需要先同步到该主目录。

在 sundries01 创建临时工作目录

::

    $ ssh sundries01.iad2.fedoraproject.org
    $ mkdir openh264-20200825

在 mm-backend01 创建临时工作目录

::

    $ ssh mm-backend01.iad2.fedoraproject.org
    $ mkdir openh264-20200825

从本地计算机同步组合

::

    $ cd openh264-20200825
    $ rsync -avhHP 32-openh264 sundries01.iad2.fedoraproject.org:/home/fedora/mohanboddu/openh264-20200825
    $ rsync -avhHP 32-openh264 mm-backend01.iad2.fedoraproject.org:/home/fedora/mohanboddu/openh264-20200825

在 sundries01 上

::

    $ cd openh264-20200825
    $ sudo rsync -avhHP 32-openh264/compose/Temporary/ /srv/web/codecs.fedoraproject.org/openh264/32/

在 mm-backend01 上

::

    $ cd openh264-20200825
    $ sudo rsync -avhHP 32-openh264/compose/Temporary/ /srv/codecs.fedoraproject.org/openh264/32/

额外信息
^^^^^^^^^^

通常应该是这样，但在某些情况下，您可能希望比正常情况更快地发布内容，您可以采取以下措施：

在 mm-backend01.iad2.fedoraproject.org 上您可以运行：

::

    # sudo -u mirrormanager /usr/local/bin/umdl-required codecs /var/log/mirrormanager/umdl-required.log

这将让镜像管理器扫描编解码器目录，并在更改时对其进行更新。

在 batcave01.iad2.fedoraproject.org 上您可以使用 ansible 强制所有代理从 sundries01 同步编解码器内容：

::

    # nsible -a '/usr/bin/rsync --delete -a --no-owner --no-group sundries01::codecs.fedoraproject.org/ /srv/web/codecs.fedoraproject.org/' proxies

镜像列表服务器应每 15 分钟更新一次。
