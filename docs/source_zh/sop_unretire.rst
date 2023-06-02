.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
取消停用软件包分支
===========================

说明
===========

有时，打包程序会要求我们取消停用以前已停用的包分支。

这通常发生在 `rawhide` 分支上，但可以想象发生在任何稳定版或其他任意分支上。

操作
======

验证包已准备好取消停用
---------------------------------------
#. 验证包是否因任何原因（例如法律或许可证问题）而停用，这将阻止其重新恢复。

#. 确保已提交 Bugzilla 以审查要取消退役的软件包。

#. 与请求者核实要取消停用请求的哪些标签需要解除阻塞。

撤销停用的提交
----------------------------
#. 连接到一个用于组合的系统

    ::

    $ ssh compose-x86-02.phx2.fedoraproject.org

#. 使用正确的发布工程凭据克隆 git-dist 包。

    ::

    $ GIT_SSH=/usr/local/bin/relengpush fedpkg --user releng clone PACKAGENAME

#. 进入克隆软件包的目录，配置 git 用户信息。

    ::

    $ cd PACKAGENAME
    $ git config --local user.name "Fedora Release Engineering"
    $ git config --local user.email "releng@fedoraproject.org"

#. Git 使用其提交hash_id在特定分支上的 dist-git 中还原 `dead.package` 文件提交。确保提交消息包含 pagure 格式的请求的 URL。

    ::

    $ git revert -s COMMIT_HASH_ID
    $ GIT_SSH=/usr/loca/bin/relengpush fedpkg --user releng push

在 Koji 中解锁包
---------------------------

#. 检查 koji 中包的分支的当前状态。

    ::

    $ koji list-pkgs --show-blocked --package=PACKAGENAME

#. 使用 koji 取消阻塞每个请求的标签。

   ::

    $ koji unblock-pkg TAGNAME PACKAGENAME

验证软件包是否孤立
------------------------------

#. 检查包所有权

   导航到 `https://src.fedoraproject.org/` 并检查包所有者。

#. 如果包是孤立的，则使用 `Release Engineering Repo`_ 
   中的 `give-package` 本将包提供给请求者。

   ::

   $ ./scripts/distgit/give-package --package=PACKAGENAME --custodian=REQUESTOR

   .. note::
       此脚本要求用户是 FAS 中 `cvsadmin` 组的成员

更新 PDC
-----------------------------------------

.. note::
    如果要取消阻止多个标签，则应为每个标签和包完成 PDC 更新步骤。

#. 使用 FAS 帐户登录 `Fedora PDC instance`_ 。

#. 检查 PDC 中每个 `TAG` 中在上一步中取消阻塞的 `PACKAGENAME` 条目。

    ::

      https://pdc.fedoraproject.org/rest_api/v1/component-branch-slas/?branch=TAG&global_component=PACKAGENAME

    .. note::
         如果此查询未返回任何信息，则它不在 PDC 中，并且可能还不是分支。请求者应该使用
         `fedpkg request-branch` 程序来请求分支。

#. 如果软件包存在于 PDC 中，则在登录时通过使用 Firefox Web 浏览器导航到
   `https://pdc.fedoraproject.org/rest_api/v1/auth/token/obtain/` URL 从 PDC 站点获取令牌。

#. 加载页面后按 F12，然后选择标有 `Network`.
   的选项卡。刷新网页并找到文件列中字符串与
   `/rest_api/v1/auth/token/obtain/` 匹配的行。

#. 右键单击指定的行，然后选择复制>复制为 cURL。将其粘贴到终端会话中并添加 `-H "Accept: application/json"` 。它应该类似于以下内容：

    ::

        $ curl 'https://pdc.fedoraproject.org/rest_api/v1/auth/token/obtain/' \
        -H 'Host: pdc.fedoraproject.org' \
        -H .0) Gecko/20100101 Firefox/57.0' \
        -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
        -H 'Accept-Language: en-US,en;q=0.5' \
        --compressed \
        -H 'Cookie: csrftoken=CSRF_TOKEN_HASH; SERVERID=pdc-web01; mellon-saml-sesion-cookie=SAML_SESSION_HASH; sessionid=SESSION_ID_HASH' \
        -H 'Connection: keep-alive' \
        -H 'Upgrade-Insecure-Requests: 1' \
        -H 'Cache-Control: max-age=0' \
        -H "Accept: application/json"

#. 使用从上一步获取的令牌运行 `Release Engineering Repo`_ 中的 `adjust-eol.py` 脚本。

    ::

    $ PYTHONPATH=scripts/pdc/ scripts/pdc/adjust-eol.py fedora MYTOKEN PACKAGENAME rpm TAG default -y

    .. note::
        本地计算机将在 `/etc/pdc.d/` 目录中包含配置信息。这就是为什么 *fedora* 可以作为参数传递而不是完整的 API 接口 URL 的原因。


.. _Fedora PDC instance: https://pdc.fedoraproject.org/
.. _Release Engineering Repo: https://pagure.io/releng
