.. SPDX-License-Identifier:    CC-BY-SA-3.0


=======================================
发布 Fedora 容器基础镜像
=======================================

说明
===========

本 SOP 涵盖了更改和发布 Fedora 容器基础映像所涉及的步骤。

Fedora 发布了 2 个容器基础镜像， `fedora` 和 `fedora-minimal` 。这些镜像可在 3 个注册表 `registry.fedoraproject.org` ， `quay.io` 和 `DockerHub` 上找到（Fedora-minimal 在 DockerHub 中不可用）。


修改基础镜像 (Kickstart)
-------------------------------

基础镜像是使用 `image-factory` 应用程序在 koji 中构建的，以构建容器镜像根文件系统 （rootfs）。
Kickstart 文件用于配置镜像的构建方式以及镜像中可用的内容，该解决方案由3个 Kickstart 组成。

`fedora-container-common <https://pagure.io/fedora-kickstarts/blob/main/f/fedora-container-common.ks>`_

`fedora-container-base <https://pagure.io/fedora-kickstarts/blob/main/f/fedora-container-base.ks>`_

`fedora-container-base-minimal <https://pagure.io/fedora-kickstarts/blob/main/f/fedora-container-base-minimal.ks>`_

对 rawhide 分支所做的更改将导致 rawhide 镜像更改，其他分支（f30、f31）应用于修改其他版本。

组合配置 (Pungi)
-----------------------------

用于组合容器镜像的配置在 pungi-fedora repository 中可用。

对于 rawhide ，配置在

https://pagure.io/pungi-fedora/blob/main/f/fedora.conf

而对于其他版本，配置在专用文件中

https://pagure.io/pungi-fedora/blob/f31/f/fedora-container.conf


发布在 registry.fedoraproject.org 和 quay.io 上
-------------------------------------------------

如果要在 registry.fp.o 和 quay.io 上发布基础镜像，可以使用以下脚本。

`sync-latest-container-base-image.sh <https://pagure.io/releng/blob/main/f/scripts/sync-latest-container-base-image.sh>`_

您需要从基础架构中的 releng composer 计算机上运行该脚本才能获得凭据。

如果您无权访问该计算机，则可以通过在 `releng tracker <https://pagure.io/releng/issues>`_ 上打开一个工单来请求发布。

然后可以按如下方式执行脚本

::

    $./sync-latest-container-base-image.sh 31
    $./sync-latest-container-base-image.sh 32

这会负责将 `fedora` 和 `fedora-minimal` 镜像推送到两个仓库中。



在 DockerHub 上发布
--------------------

在 DockerHub 上发布有点不同，因为Fedora在那里是一个 “offical” 镜像。为了在那里发布新镜像，我们必须在以下存储库中更新 Dockerfile 和 rootfs 压缩包。

`docker-brew-fedora <https://github.com/fedora-cloud/docker-brew-fedora>`_.

有关如何运行脚本的详细信息，请参阅

`README <https://github.com/fedora-cloud/docker-brew-fedora/blob/main/README.md>`_.
