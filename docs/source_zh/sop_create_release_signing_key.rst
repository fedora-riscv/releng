.. SPDX-License-Identifier:    CC-BY-SA-3.0


==========================
创建发布签名密钥
==========================

说明
===========
在每个正在开发的版本开始时，都会为其创建一个新的包签名密钥。该密钥用于证明Fedora构建和分发的包的真实性。此密钥将用于为公开测试和最终发布的所有包签名。

操作
======

Sigul
-----
Sigul是保存我们密钥的签名服务器。为了使用新密钥，必须创建密钥，并且必须授予对该密钥的访问权限。使用 ``new-key`` , ``grant-key-access`` ，和 ``change-passphrase`` 命令。

::

    $ sigul new-key --help
    usage: client.py new-key [options] key

    Add a key

    options:
      -h, --help            show this help message and exit
      --key-admin=USER      Initial key administrator
      --name-real=NAME_REAL
                            Real name of key subject
      --name-comment=NAME_COMMENT
                            A comment about of key subject
      --name-email=NAME_EMAIL
                            E-mail of key subject
      --expire-date=YYYY-MM-DD
                            Key expiration date

    $ sigul grant-key-access --help
    usage: client.py grant-key-access key user

    Grant key access to a user

    options:
      -h, --help  show this help message and exit

    $ sigul change-passphrase --help
    usage: client.py change-passphrase key

    Change key passphrase

    options:
      -h, --help  show this help message and exit

例如，如果我们想创建Fedora 23签名密钥，我们将执行以下操作：

#. 登录到配置为运行sigul客户端的系统。
#. 在提示时使用强密码短语创建密钥

   ::

        $ sigul new-key --key-admin ausil --key-type gnupg \
                --gnupg-name-real Fedora \
                --gnupg-name-comment 23 \
                --gnupg-name-email fedora-23-primary@fedoraproject.org fedora-23

   对于EPEL

   ::

        $ sigul new-key --key-admin ausil --key-type gnupg \
                --gnupg-name-real "Fedora EPEL" \
                --gnupg-name-comment 7 \
                --gnupg-name-email epel@fedoraproject.org epel-7

#. 等一下熵。这可能需要几分钟时间。
#. 对于Fedora，还要创建IMA签名密钥

   ::

        $ sigul new-key --key-admin ausil --key-type ECC fedora-23-ima

#. 将密钥访问权限授予将对包进行签名的Fedora帐户持有者，并使用临时密码短语对其进行保护。例如， ``CHANGEME.``。对Fedora的-ima密钥也执行同样的操作。

   ::

        $ sigul grant-key-access fedora-23 kevin

.. note::
    **重要事项：** 授予自动签名用户访问权限，因为这是自动签名所需的，然后重新启动自动签名服务

#. 向签名者提供密钥名称和临时密码短语。如果他们没有响应，则撤销访问权限，直到他们准备好更改密码短语为止。签名者可以使用 ``change-passphrase`` 命令更改他们的密码：

   ::

        $ sigul change-passphrase fedora-23

#. 当您的sigul证书到期时，您将需要运行：

   ::

        certutil -d ~/.sigul -D -n sigul-client-cert

   要删除旧证书，则

   ::

        sigul_setup_client

   来添加一个新的。

fedora-repos
------------
fedora-repos软件包中包含一份公钥信息。rpm使用它来验证遇到的文件上的签名。目前，fedora-repos软件包有一个单独的密钥文件，以密钥的版本和密钥所在的arch命名。
为了继续我们的示例，该文件将命名为 ``RPM-GPG-KEY-fedora-27-primary`` ，这是Fedora 27的主要arch密钥。要创建此文件，请使用sigul中的 ``get-public-key`` 命令：

::

    $ sigul get-public-key fedora-27 > RPM-GPG-KEY-fedora-27-primary

将此文件添加到repo中，并为新版本更新archmap文件。

::

    $ git add RPM-GPG-KEY-fedora-27-primary

然后为rawhide (``FIXME: this should be its own SOP``)制作一个新的fedora-repos构建

getfedora.org
-------------
getfedora.org/keys列出了关于我们所有密钥的信息。我们需要让网站团队知道我们已经创建了一个新的密钥，以便他们可以将其添加到列表中。

我们通过在他们的pagure实例
https://pagure.io/fedora-websites/
中提交问题来做到这一点，我们应该将他们指向这个SOP

网络团队SOP
^^^^^^^^^^^^

::

    # from git repo root
    cd fedoraproject.org/
    curl $KEYURL > /tmp/newkey
    $EDITOR update-gpg-keys # Add key ID of recently EOL'd version to obsolete_keys
    ./update-gpg-key /tmp/newkey
    gpg static/fedora.gpg # used to verify the new keyring
    # it should look something like this:
    # pub  4096R/57BBCCBA 2009-07-29 Fedora (12) <fedora@fedoraproject.org>
    # pub  4096R/E8E40FDE 2010-01-19 Fedora (13) <fedora@fedoraproject.org>
    # pub  4096R/97A1071F 2010-07-23 Fedora (14) <fedora@fedoraproject.org>
    # pub  1024D/217521F6 2007-03-02 Fedora EPEL <epel@fedoraproject.org>
    # sub  2048g/B6610DAF 2007-03-02 [expires: 2017-02-27]
    # it must only have the two supported versions of fedora, rawhide and EPEL
    # also verify that static/$NEWKEY.txt exists
    $EDITOR data/content/{keys,verify}.html # see git diff 1840f96~ 1840f96

sigulsign_unsigned
------------------
``sigulsign_unsigned.py`` 是发布工程师用来在koji中对内容签名的脚本。这个脚本有一个硬编码的密钥和密钥别名列表，在创建新密钥时需要更新这些密钥和别名。

将关键细节添加到 ``sigulsign_unsigned.py`` 脚本顶部附近的 ``KEYS`` 字典中。它在位于 ``ssh://git@pagure.io/releng.git`` 的Release Engineering git仓库中的 ``scripts`` 目录中。
您需要知道密钥ID才能插入正确的信息：

::

    $ gpg <key block from sigul get-public-key>

公钥服务器
-----------------
我们在创建密钥时将密钥上传到公钥服务器。要做到这一点，我们需要从sigul获取ascii密钥块，确定密钥ID，将他们的密钥导入我们的本地密钥环，然后将其上传到密钥服务器。

::

    $ sigul get-public-key fedora-13 > fedora-13
    $ gpg fedora-13 (The ID is the "E8E40FDE" part of 4096R/E8E40FDE)
    $ gpg --import fedora-13
    $ gpg --send-keys E8E40FDE

pungi-fedora
------------
夜间compose配置来自 https://pagure.io 上的pungi-fedora项目。我们需要创建一个pull request来拉取新密钥。

::

    $ git clone ssh://git@pagure.io/<your fork path>/pungi-fedora.git
    $ cd pungi-fedora
    $ vim *conf
    <set key value in sigkeys = line >
    $ git commit -m 'Add new key'
    $ git push
    $ file a Pull Request


Koji
----
Koji有一个垃圾收集程序，它可以找到符合删除标准的构建，以节省空间。部分标准与构建是否已使用密钥进行签名有关。
如果收集程序不知道某个密钥，它将忽略构建。因此，当我们创建新的密钥时，我们需要通知这些密钥的实用性，否则构建可能会堆积起来。垃圾收集程序的配置位于ansible中。

在基础设施ansible git仓库的克隆上，编辑roles/koji_hub/templates/koji-gc.conf.j2文件：

::

    diff --git a/roles/koji_hub/templates/koji-gc.conf.j2 b/roles/koji_hub/templates/koji-gc.conf.j2
    index 9ecb750..9c48a8e 100644
    --- a/roles/koji_hub/templates/koji-gc.conf.j2
    +++ b/roles/koji_hub/templates/koji-gc.conf.j2
    @@ -35,6 +35,7 @@ key_aliases =
         81B46521    fedora-24
         FDB19C98    fedora-25
         64DAB85D    fedora-26
    +    F5282EE4    fedora-27
         217521F6    fedora-epel
         0608B895    fedora-epel-6
         352C64E5    fedora-epel-7
    @@ -52,6 +53,7 @@ unprotected_keys =
         fedora-24
         fedora-25
         fedora-26
    +    fedora-27
         fedora-extras
         redhat-beta
         fedora-epel
    @@ -91,6 +93,7 @@ policy =
         sig fedora-24 && age < 12 weeks :: keep
         sig fedora-25 && age < 12 weeks :: keep
         sig fedora-26 && age < 12 weeks :: keep
    +    sig fedora-27 && age < 12 weeks :: keep
         sig fedora-epel && age < 12 weeks :: keep
         sig fedora-epel-6 && age < 12 weeks :: keep
         sig fedora-epel-7 && age < 12 weeks :: keep

在这种情况下，fedora-epel密钥被添加到密钥别名列表中，然后在未受保护的_keys列表中被引用，最后创建了一个策略，用于保持使用该密钥签名的构建的时间。

一旦你做出了commit和push改动。构建系统将在下次刷新时接受此更改。

验证
============
我们可以验证该密钥是在sigul中创建的，正确的用户可以访问该密钥，该密钥已添加到fedora发布包中，网站已使用正确的密钥更新，sigulsign_unsigned已正确更新，并且该密钥已成功更新到公钥服务器。

sigul
-----
使用 ``list-keys`` 命令验证密钥是否确实添加到了sigul中：

::

    $ sigul list-keys
    Administrator's password:
    fedora-10
    fedora-10-testing
    fedora-11
    fedora-12
    fedora-13

我们的新钥匙应该在名单上。此命令需要 **your** 管理密码。

使用 ``list-key-users`` 命令验证所有签名者是否具有访问权限：

::

        $ sigul list-key-users fedora-13
        Key passphrase:
        jkeating
        jwboyer

此命令需要 **your** 密钥短语作为有问题的密钥。

fedora-release
--------------
要验证密钥是否已正确添加到此软件包，请从koji下载最新版本并在其上运行rpm2cpio，然后在密钥文件上运行gpg：

::

    $ koji download-build --arch noarch --latest f27 fedora-repos
    fedora-repos-rawhide-27-0.1.noarch.rpm                  | 7.3 kB  00:00:00
    fedora-repos-27-0.1.noarch.rpm                          |  87 kB  00:00:00
    $ rpmdev-extract fedora-repos-27-0.1.noarch.rpm
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-27-fedora
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-10-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-10-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-10-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-10-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-10-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-11-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-11-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-11-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-11-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-11-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-12-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-12-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-12-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-12-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-12-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-arm
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-mips
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-14-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-14-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-14-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-arm
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-arm
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-arm
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-arm
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-7-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-8-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-8-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-8-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-8-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-8-primary-original
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-8-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-ia64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-primary-original
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-x86_64
    fedora-repos-27-0.1.noarch/etc/yum.repos.d
    fedora-repos-27-0.1.noarch/etc/yum.repos.d/fedora-cisco-openh264.repo
    fedora-repos-27-0.1.noarch/etc/yum.repos.d/fedora-updates-testing.repo
    fedora-repos-27-0.1.noarch/etc/yum.repos.d/fedora-updates.repo
    fedora-repos-27-0.1.noarch/etc/yum.repos.d/fedora.repo

    $ gpg2 fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-primary
    pub   rsa4096 2017-02-21 [SCE]
          860E19B0AFA800A1751881A6F55E7430F5282EE4
    uid           Fedora 27 (27) <fedora-27@fedoraproject.org>
        pub  4096R/E8E40FDE 2010-01-19 Fedora (13) <fedora@fedoraproject.org>

您可能希望在临时目录中执行此操作，以便轻松清理。

getfedora.org
-----------------
您可以简单地浏览到 https://getfedora.org/keys 以验证密钥是否已上传。

sigulsign_unsigned
------------------
测试密钥添加是否正确的最佳方法是使用密钥对包进行签名，就像我们新建的fedora repo包一样。

::

    $ ./sigulsign_unsigned.py fedora-13 fedora-release-13-0.3
    Passphrase for fedora-13:

命令应该干净地退出。

公钥服务器
------------------
可以使用gpg中的 <code>search-keys</code> 命令在公共服务器上查找密钥：

::

    $ gpg2 --search-keys "Fedora (13)"
    gpg: searching for "Fedora (13)" from hkp server subkeys.pgp.net
    (1) Fedora (13) <fedora@fedoraproject.org>
          4096 bit RSA key E8E40FDE, created: 2010-01-19
    ...

Koji
----
通过bastion.fedoraproject.org登录到koji02.phx2.fedoraproject.org。

验证 ``/etc/koji-gc/koji-gc.conf`` 中是否有新密钥。

运行之前请考虑
=======================

目前什么都没有。

