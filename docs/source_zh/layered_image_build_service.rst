.. SPDX-License-Identifier:    CC-BY-SA-3.0

=================================
Fedora 分层镜像构建系统
=================================

Fedora 分层镜像构建系统旨在提供 Fedora 官方二进制制品的新类型。目前，我们生产两种主要类型的制
品： RPM 和镜像。RPMs 是从 dist-git 中的 specfiles 在 `Koji`_ 中创建的。镜像有不同的格式，但
是共同点是从 kickstart 文件中在 Koji 中创建的——这包括官方的 Fedora Docker 基础镜像。此更改
引入了一种新类型的镜像，即 `Docker`_ 分层镜像，它是从 Dockerfile 创建的，并在该基础镜像之上构建。


分层镜像构建服务架构
========================================

::

    +------------------------------+
    | Future Items to Integrate    |
    +------------------------------+
    | +--------------------------+ |
    | |PDC Integration           | |
    | +--------------------------+ |
    | |New Hotness               | |
    | +--------------------------+ |
    | |Other???                  | |
    | +--------------------------+ |
    |  Magical Future              |
    |                              |
    +------------------------------+



           +------------------+
           |Fedora            |
           |Users/Contributors|
           +--------+---------+
                    ^
                    |                                   +----------------+
                    |                                   |  Fedora        |
            +-------+-----------+                       |  Layered Image |
            | Fedora Production |                       |  Maintainers   |
            | Docker Registry   |                       |                |
            +-------------------+                       +-------+--------+
                    ^                                           |
                    |                                           V
                    |                       +-------------------+--+
        +-----------+------------+          |                      |
        |   RelEng Automation    |          | +------------------+ |
        |      (Release)         |          | |Dockerfile        | |
        +-----------+------------+          | +------------------+ |
                    ^                       | |App "init" scripts| |
                    |                       | +------------------+ |
                    |                       | |Docs              | |
          +---------+------------+          | +------------------+ |
          | Taskotron            |          |  DistGit             |
          | Automated QA         |          |                      |
          +---------+-------+----+          +-----------+----------+
                    ^       ^                           |
                    |       |                           |
                    |       |                           |
                    |       |                           |
                    |       +-------------------+       |
                    |                           |       |
             [docker images]                    |       |
                    |                           |       |
                    |                       [fedmsg]    |
    +---------------+-----------+               |       |
    |                           |               |       +---------------+
    | +----------------------+  |               |                       |
    | |Intermediate Docker   |  |        +------+-------------------+   |
    | |Images for OSBS Builds|  |        |                          |   |
    | +----------------------+  |        | +----------------------+ |   |
    | |Layered Images        |  |        | |containerbuild plugin | |   |
    | +----------------------+  |        | +----------------------+ |   |
    | |docker|distribution   |  |        | |rpmbuilds             | |   |
    | +----------------------+  |        | +----------------------+ |   |
    |  Registry                 |        |  koji                    |   |
    |                           |        |                          |   |
    +-----+----+----------------+        +-----+---+----+-----------+   |
          |    ^                               |   ^        ^           |
          |    |                               |   |        |           |
          |    |   +---------------------------+   |        |           |
          |    |   |       [osbs-client api]       |        |           |
          |    |   |   +---------------------------+        |           |
          |    |   |   |                                    |           |
          |    |   |   |                                    |           |
          V    |   V   |                                    |           |
       +--+----+---+---+---+                                |           V
       |                   |                        +-------------------+---+
       | +--------------+  |                        |fedpkg container-build +
       | |OpenShift v3  |  |                        +-----------------------+
       | +--------------+  |
       | |Atomic Reactor|  |
       | +--------------+  |
       |  OSBS             |
       |                   |
       +-------------------+


    [--------------------- Robosignatory ------------------------------------]
    [ 每次图像被标记或更改名称时 Robosignatory都会对其进行签名                      ]
    [                                                                        ]
    [ NOTE: 为了简洁起见，在图中保留了它的注入点                                   ]
    [------------------------------------------------------------------------]


分层映像构建系统组件
=====================================

分层映像构建系统的主要方面是：

* Koji

  * koji-containerbuild 插件

* OpenShift Origin v3
* Atomic Reactor
* osbs-client tools
* A docker registry

  * docker-distribution

* Taskotron
* fedmsg
* RelEng Automation


该构建系统的设置是这样的，Fedora 分层镜像维护者将通过 ``fedpkg container-build`` 命令提交一个构建
到 `DistGit`_ 内的 ``containers`` 命名空间中，这将触发使用 `osbs-client`_ 工具在 `OpenShift`_ 中调度构建，
这将创建一个自定义的 `OpenShift Build`_ 构建，它将使用我们创建的预制的 buildroot Docker 镜像。
`Atomic Reactor`_ （ ``atomic-reactor`` ）实用程序将在 buildroot 中运行并准备构建容器，在其中执行实际
的构建操作，还将维护上传 `Content Generator`_ 元数据回 `Koji`_ 并将构建后的镜像上传到候选 docker 注册
表。这将在一个带有 iptables 规则的主机上运行，该规则限制了对 docker 桥的访问，这是我们将进一步限
制 buildroot 对外部世界进行验证的信息来源的方式。

完成的分层镜像构建存储在候选 docker 注册表中，然后使用 `Taskotron`_ 拉取镜像并执行测试。Taskotron 测
试由 `Koji`_ 发出的 `fedmsg`_ 消息触发，一旦构建完成就会发出。测试完成后，taskotron 将发送 fedmsg，然后
由 `RelEng Automation` 引擎捕获，该引擎将运行自动发布任务，以将分层镜像推送到生产空间中的稳定 docker 注册表
中，供最终用户使用。

请注意，每次将分层镜像标记到新的注册表中时，最终都会更改其名称，因此 `Robosignatory`_ 将自动签署新的镜像。
这也将作为自动化发布流程的一部分发生，因为该镜像将从候选 docker 注册表中标记到生产 docker 注册表中，以
将镜像“升级”为稳定版本。

Koji
----

`Koji`_ 是 Fedora 构建系统。


koji-containerbuild 插件
--------------------------

`koji-containerbuild`_ 插件集成了 Koji 和 OSBS，因此 koji 可以调度构建，并通过导入元数据、日志、构建数据和构建工件集成到构建系统中。

OpenShift Origin v3
-------------------

`OpenShift Origin v3`_ 是一个开源容器平台，建立在
`kubernetes`_ 和 `Docker`_ 之上。这提供了所需的系统的许多方面，包括 Docker 映像的构建管道，其中包含自定义构建配置文件、镜像流和基于系统内事件的触发器。

Atomic Reactor
--------------

`Atomic Reactor`_ 是一个实用程序，它允许从其他容器内构建容器，提供钩子以触发构建自动化以及提供自动集成许多其他实用程序和服务的插件。


osbs-client 工具
-----------------

`osbs-client`_ 工具允许用户使用一组简单的命令行实用程序访问
`OpenShift Origin v3`_ 的构建功能。


docker-registry
---------------

`docker-registry`_ 是一个无状态、高度可扩展的服务器端应用程序，用于存储并允许您分发 Docker 镜像。

有许多不同的 docker-registry 实现，Fedora 分层镜像构建系统支持两个主要的实现。

docker-distribution
~~~~~~~~~~~~~~~~~~~

`docker-distribution`_ 注册表被认为是 Docker 上游的“v2 注册表”，因此它被上游用于实现 docker-registry 的新版本 2 规范。

Fedora 生产注册表
~~~~~~~~~~~~~~~~~~~~~~~~~~

在撰写本文时，这方面的实施细节仍然未知，并将在以后更新。有关当前状态和实现说明，请访问 `FedoraDockerRegistry`_ 页面。

Taskotron
---------

`Taskotron`_ 是一个自动化任务执行框架，编写在
`buildbot`_ 之上，目前执行许多 Fedora 自动化 QA 任务，我们将添加分层映像自动化 QA 任务。测试本身将在DistGit中进行，并由分层映像维护者维护。

RelEng Automation
-----------------

`RelEng Automation`_ 是一项持续的努力，通过使用 `Ansible`_ 并由 `fedmsg`_ 通过
`Loopabull`_ 驱动，以执行基于 fedmsg 事件的 Ansible Playbook，从而尽可能多地自动化 RelEng 流程。

Robosignatory
-------------

`Robosignatory`_ 是一个 fedmsg 的客户，它会自动对工件进行签名，并将用于自动对Docker分层映像进行签名，以便客户端工具和最终用户进行验证。

未来的集成
-------------------

将来， `Fedora Infrastructure`_ 的其他各种组件可能会被合并。

PDC
~~~

`PDC`_ 是 Fedora 对 `Product Definition Center`_ 的实现，它允许 Fedora 以一种可以查询的方式维护每个 Compose 及其所有内容的数据库，并以编程方式用于决策。

The New Hotness
~~~~~~~~~~~~~~~

`The New Hotness`_ 是一个 `fedmsg`_ 的客户，它监听 release-monitoring.org 并提交bugzilla错误作为响应（通知打包者他们可以更新他们的软件包）。

.. _Ansible: http://ansible.com/
.. _buildbot: http://buildbot.net/
.. _kubernetes: http://kubernetes.io/
.. _PDC: https://pdc.fedoraproject.org/
.. _fedmsg: http://www.fedmsg.com/en/latest/
.. _Koji: https://fedoraproject.org/wiki/Koji
.. _Docker: https://github.com/docker/docker/
.. _pulp-crane: https://github.com/pulp/crane
.. _OpenShift: https://www.openshift.org/
.. _Robosignatory: https://pagure.io/robosignatory
.. _OpenShift Origin V3: https://www.openshift.org/
.. _Taskotron: https://taskotron.fedoraproject.org/
.. _docker-registry: https://docs.docker.com/registry/
.. _Loopabull: https://github.com/maxamillion/loopabull
.. _RelEng Automation: https://pagure.io/releng-automation
.. _osbs-client: https://github.com/projectatomic/osbs-client
.. _docker-distribution: https://github.com/docker/distribution/
.. _Atomic Reactor: https://github.com/projectatomic/atomic-reactor
.. _The New Hotness: https://github.com/fedora-infra/the-new-hotness
.. _Fedora Infrastructure: https://fedoraproject.org/wiki/Infrastructure
.. _koji-containerbuild:
    https://github.com/release-engineering/koji-containerbuild
.. _Fedora Mirror Network:
    https://fedoraproject.org/wiki/Infrastructure/Mirroring
.. _koji-containerbuild:
    https://github.com/release-engineering/koji-containerbuild
.. _Fedora Docker Registry:
    https://fedoraproject.org/wiki/Changes/FedoraDockerRegistry
.. _DistGit:
    https://fedoraproject.org/wiki/Infrastructure/VersionControl/dist-git
.. _OpenShift Build:
    https://docs.openshift.org/latest/dev_guide/builds.html
.. _Content Generator:
    https://fedoraproject.org/wiki/Koji/ContentGenerators
.. _FedoraDockerRegistry:
    https://fedoraproject.org/wiki/Changes/FedoraDockerRegistry
.. _Product Definition Center:
    https://github.com/product-definition-center/product-definition-center
