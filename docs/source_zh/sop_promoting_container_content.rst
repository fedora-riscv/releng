.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
推广容器内容
===========================

说明
===========
尽管内容的推广旨在实现完全自动化，但有时需要或希望将候选的注册表中的内容升级到稳定的注册表中。以下是使用 `skopeo`_ 完成此操作的方法。

操作
======

此操作应由 ``compose-x86-01.phx2.fedoraproject.org`` `FAS`_ 组成员的用户在
``sysadmin-releng`` 上执行。

容器映像应由请求者提供，他们将在 `Fedora Layered Image Build
System`_ 中获得来自其容器构建的信息。它将有一个类似于
``candidate-registry.fedoraproject.org/f26/foo:0.1-1.f26container`` 的名称。

同步候选注册表和生产注册表之间的内容，实现“推广”。请在下面的示例中使用实际的镜像名称替换 ``$IMAGE_NAME`` 。（即 ``candidate-registry.fedoraproject.org`` 后面的所有内容，所以使用上面的示例，则
``$IMAGE_NAME`` 将是 ``f26/foo:0.1-1.f26container`` 。）

::

    $ sudo skopeo copy \
        --src-cert-dir /etc/docker/certs.d/candidate-registry.fedoraproject.org/ \
        --dest-cert-dir /etc/docker/certs.d/registry.fedoraproject.org/ \
        docker://candidate-registry.fedoraproject.org/$IMAGE_NAME \
        docker://registry.fedoraproject.org/$IMAGE_NAME

验证
============

为了验证，我们需要检查稳定的注册表，再次使用 `skopeo`_
以确保图像元数据存在。

::

    $ skopeo inspect docker://registry.fedoraproject.org/$IMAGE_NAME

在此 JSON 输出中，您将看到一个名为 ``RepoTags`` 的列表元素，其中应该列出 ``$VERSION-$RELEASE`` ，按照上面的示例，此条目将是 ``0.1-1.f26container`` 。

.. _skopeo: https://github.com/projectatomic/skopeo
.. _FAS: https://admin.fedoraproject.org/accounts/
.. _Fedora Layered Image Build System:
    https://docs.pagure.org/releng/layered_image_build_service.html
