.. SPDX-License-Identifier:    CC-BY-SA-3.0


================================================
Fedora 发布工程故障排除指南
================================================

Fedora Release Engineering 包含许多不同的系统、许多不同的代码库和多个工具。不用说，事情可能会变得非常复杂。
这个方面对于想要参与其中的新手来说并不是很友好。本指南旨在为那些新到流程、系统、代码库和工具的人提供教育，并作为
那些不是新手但可能幸运地没有需要在最近的记忆中诊断问题的人的参考。

我们当然无法记录系统中可能出现的每个可能出现问题的组件，但希望随着时间的推移，本文档将作为适当的知识库，用于以下
所列主题的参考和教育目的。


组合
=======

如果组合的内容出错，可以在许多地方查找信息。下面将逐一讨论。

releng-cron 列表
----------------

组合输出日志通过电子邮件发送到 releng-cron 邮件列表。检查 `releng-cron 邮件列表存档`_ 找到最新的输出并查看是一种很好的做法。

.. _compose-machines:

组合机器
----------------

如果 `releng-cron 邮件列表存档`_ 被证明是没有用的，你可以继续在 Fedora 基础设施中的主要的组合机器上检查组合本身的内容。在撰写本文时，根据您要查找的特定组合，有多台计算机：

* 两周的原子夜间组合

  * ``compose-x86-01.phx2.fedoraproject.org``

* 分支组合

  * ``branched-composer.phx2.fedoraproject.org``

* Rawhide 组合

  * ``rawhide-composer.phx2.fedoraproject.org``

根据您要搜索的特定组合，将取决于您最终将检查的完整路径：

* 对于两周原子，您将在
  ``/mnt/fedora_koji/compose/`` 中找到组合的输出
* 对于版本候选/测试候选组合，您将在 ``/mnt/koji/compose/`` 中找到组合的输出

.. note::
    mock 日志可能不再可用。mock chroots 在随后的组合运行中被重写。

您还可以检查 mock 日志，以查看您感兴趣的组合是否仍然存在。通过检查相应的组合 mock 配置（以下仅为本文撰写
时提供的示例），找到您要查找的特定 mock chroot 目录名称（将驻留在 ``/var/lib/mock/`` 中）：

::

    $ ls /etc/mock/*compose*
        /etc/mock/fedora-22-compose-aarch64.cfg  /etc/mock/fedora-branched-compose-aarch64.cfg
        /etc/mock/fedora-22-compose-armhfp.cfg   /etc/mock/fedora-branched-compose-armhfp.cfg
        /etc/mock/fedora-22-compose-i386.cfg     /etc/mock/fedora-branched-compose-i386.cfg
        /etc/mock/fedora-22-compose-x86_64.cfg   /etc/mock/fedora-branched-compose-x86_64.cfg
        /etc/mock/fedora-23-compose-aarch64.cfg  /etc/mock/fedora-rawhide-compose-aarch64.cfg
        /etc/mock/fedora-23-compose-armhfp.cfg   /etc/mock/fedora-rawhide-compose-armhfp.cfg
        /etc/mock/fedora-23-compose-i386.cfg     /etc/mock/fedora-rawhide-compose-i386.cfg
        /etc/mock/fedora-23-compose-x86_64.cfg   /etc/mock/fedora-rawhide-compose-x86_64.cfg

运行组合本身
----------------------------

如果您在那里没有找到相应的信息并且仍然需要进行调试，那么也许是时候自己运行组合了。所需的确切命令可以在各自的组合机器上的计划作业中
找到，该信息可以在 :ref:`compose-machines` 部分找到。另请注意，每个相应的组合命令都应该从其各自的组合机器上运行，如 :ref:`compose-machines` 部分所述。

以下是一个示例，将组合目录设置为您的 ``用户名-debug.1`` ，末尾的 ``.1`` 是组合的递增运行的常见符号。如果您需要另一个组合，请将其递增到 ``.2`` 并继续。这有助于对比组合。

.. note::
    建议在 `screen`_ 或 `tmux`_ 中运行以下命令

::

    $ TMPDIR=`mktemp -d /tmp/twoweek.XXXXXX` && cd $TMPDIR \
        && git clone -n https://pagure.io/releng.git && cd releng && \
        git checkout -b stable twoweek-stable && \
        LANG=en_US.UTF-8 ./scripts/make-updates 23 updates $USER-debug.1

上面的命令是从 ``twoweek-atomic`` cron 作业中提取的，只更改了最后一个参数。这用作输出目录的名称。

组合可能需要一些时间才能运行，因此如果您有一段时间没有看到输出，请不要担心。这应该为您提供了进一步调试和/或诊断所需的所有信息。如果有疑问，请在 ``irc.libera.chat`` 上询问 ``#fedora-releng`` 。

Docker 层次化镜像构建服务
==================================

`Docker 层次化镜像构建服务`_ 是使用多种技术构建的，例如 `OpenShift`_ 、 `osbs-client`_ 和 `koji-containerbuild`_ 插件，当结合在一起时通常被称为 OpenShift 构建服务实例（OSBS）。
需要注意的是， `OpenShift`_ 是基于 `kubernetes`_ 构建的 `kubernetes`_ 发行版，具有许多内置于 Kubernetes 之上的功能，例如用作构建服务基础的 `构建原语`_ 。这些信息有望阐明下面使用的某些术语和命令。

构建可能失败或挂起的几个“常见”场景都需要对构建系统进行某种类型的检查。

构建在计划后似乎停止
--------------------------------------------

如果通过 koji 安排的构建似乎已停滞并且不处于 ``free`` 状态（即已被安排），则管理员需要 ssh 到 ``osbs-master01`` 或 ``osbs-master01.stg`` （取决于阶段与生产）并检查构建本身。

::

    $ oc status
    In project default on server https://10.5.126.216:8443

    svc/kubernetes - 172.30.0.1 ports 443, 53, 53

    bc/cockpit-f24 custom build of git://....
      build #8 succeeded 7 weeks ago
      build #9 failed 33 minutes ago

    $ oc describe build/cockpit-f24-9
    # lots of output about status of the specific build

    $ oc logs build/cockpit-f24-9
    # extremely verbose logs, these should in normal circumstances be found in
    # the koji build log post build

在上述命令中找到的信息通常可以识别问题。

构建失败，但 Koji 任务中没有日志输出
------------------------------------------------------

有时 Koji 与 OSBS 之间存在通信问题，导致故障未在 Koji 中列出但没有所有日志。可以通过检查任务输出中列出的 Koji 构建器上的 ``kojid`` 日志来诊断这些问题。

例如：

::

    $ fedpkg container-build
    Created task: 90123598
    Task info: http://koji.stg.fedoraproject.org/koji/taskinfo?taskID=90123598
    Watching tasks (this may be safely interrupted)...
    90123598 buildContainer (noarch): free
    90123598 buildContainer (noarch): free -> open (buildvm-04.stg.phx2.fedoraproject.org)
      90123599 createContainer (x86_64): free
      90123599 createContainer (x86_64): free -> open (buildvm-02.stg.phx2.fedoraproject.org)
      90123599 createContainer (x86_64): open (buildvm-02.stg.phx2.fedoraproject.org) -> closed
      0 free  1 open  1 done  0 failed
    90123598 buildContainer (noarch): open (buildvm-04.stg.phx2.fedoraproject.org) -> FAILED: Fault: <Fault 2001: 'Image build failed. OSBS build id: cockpit-f24-9'>
      0 free  0 open  1 done  1 failed

    90123598 buildContainer (noarch) failed

在这个例子中，buildContiner 任务在 ``buildvm-04.stg`` 上被安排并运行，实际的 createContainer 任务
在 ``buildvm-02.stg`` 上进行，而且我们将从 ``buildvm-02.stg`` 开始寻找与 OSBS 通信失败的错误，因为这是与外部系统联系的接触点。

日志可以在 ``/var/log/kojid.log`` 中找到，或者必要时，检查相应的 koji hub。通常，您会想从与 OSBS 的第一个接触点
“倒退”，因此在上面的例子中，首先检查 ``buildvm-02.stg`` ，然后如果在前一个机器的日志中没有发现有用的信息，则转移到 ``buildvm-04.stg`` ，如果涉及的构建器机器都没有提供有用的日志信息，则再次转移到 koji hub。

构建失败，因为它无法访问网络资源
------------------------------------------------------

有时，防火墙规则在环境中的某个 OpenShift 节点上会搞砸。这可能会导致类似于以下内容的输出：

::

    $ fedpkg container-build --scratch
    Created task: 90066343
    Task info: http://koji.stg.fedoraproject.org/koji/taskinfo?taskID=90066343
    Watching tasks (this may be safely interrupted)...
    90066343 buildContainer (noarch): free
    90066343 buildContainer (noarch): free -> open (buildvm-03.stg.phx2.fedoraproject.org)
      90066344 createContainer (x86_64): open (buildvm-04.stg.phx2.fedoraproject.org)
      90066344 createContainer (x86_64): open (buildvm-04.stg.phx2.fedoraproject.org) -> FAILED: Fault: <Fault 2001: "Image build failed. Error in plugin distgit_fetch_artefacts: OSError(2, 'No such file or directory'). OSBS build id: scratch-20161102132628">
      0 free  1 open  0 done  1 failed
    90066343 buildContainer (noarch): open (buildvm-03.stg.phx2.fedoraproject.org) -> closed
      0 free  0 open  1 done  1 failed


如果我们转到OSBS主服务器并运行以下命令，我们将看到根本问题：

::

    # oc logs build/scratch-20161102132628
    Error from server: Get https://osbs-node02.stg.phx2.fedoraproject.org:10250/containerLogs/default/scratch-20161102132628-build/custom-build: dial tcp 10.5.126.213:10250: getsockopt: no route to host

    # ping 10.5.126.213
    PING 10.5.126.213 (10.5.126.213) 56(84) bytes of data.
    64 bytes from 10.5.126.213: icmp_seq=1 ttl=64 time=0.299 ms
    64 bytes from 10.5.126.213: icmp_seq=2 ttl=64 time=0.299 ms
    64 bytes from 10.5.126.213: icmp_seq=3 ttl=64 time=0.253 ms
    64 bytes from 10.5.126.213: icmp_seq=4 ttl=64 time=0.233 ms
    ^C
    --- 10.5.126.213 ping statistics ---
    4 packets transmitted, 4 received, 0% packet loss, time 3073ms
    rtt min/avg/max/mdev = 0.233/0.271/0.299/0.028 ms

    # http get 10.5.126.213:10250

    http: error: ConnectionError: HTTPConnectionPool(host='10.5.126.213', port=10250): Max retries exceeded with url: / (Caused by NewConnectionError('<requests.packages.urllib3.connection.HTTPConnection object at 0x7fdab064b320>: Failed to establish a new connection: [Errno 113] No route to host',)) while doing GET request to URL: http://10.5.126.213:10250/


在上面的输出中，我们可以看到我们确实与节点有网络连接，但我们无法连接到应该侦听端口 ``10250`` 的 OpenShift 服务。

要解决此问题，您需要 ssh 到无法通过端口 ``10250`` 连接到的 OpenShift 节点，然后运行以下命令。这应该可以解决问题。

::

    iptables -F && iptables -t nat -F && systemctl restart docker && systemctl restart origin-node

.. _tmux: https://tmux.github.io/
.. _kubernetes: http://kubernetes.io/
.. _OpenShift: https://www.openshift.org/
.. _screen: https://www.gnu.org/software/screen/
.. _osbs-client: https://github.com/projectatomic/osbs-client
.. _构建原语: https://docs.openshift.org/latest/dev_guide/builds.html
.. _koji-containerbuild:
    https://github.com/release-engineering/koji-containerbuild
.. _releng-cron 邮件列表存档:
    https://lists.fedoraproject.org/archives/list/releng-cron@lists.fedoraproject.org/
.. _Docker Layered Image Build Service:
    https://fedoraproject.org/wiki/Changes/Layered_Docker_Image_Build_Service
