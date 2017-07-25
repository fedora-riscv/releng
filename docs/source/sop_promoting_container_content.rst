.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
Promoting Container Content
===========================

Description
===========
Even though the promotion of content is aimed to be fully automated, sometimes
there is the need or desire to promote content from the candidate registry to
the stable registry. Below is how to accomplish this using `skopeo`_.

Action
======

This action should be performed on ``compose-x86-01.phx2.fedoraproject.org`` by
an user who is a member of the ``sysadmin-releng`` `FAS`_ Group.

The container image should be provided by the requester, they will have the
information from their container build in the `Fedora Layered Image Build
System`_. It will have a name resembling
``candidate-registry.fedoraproject.org/f26/foo:0.1-1.f26container``.

Sync content between the candidate registry and production registry, effectively
"promoting it". Substitute the ``$IMAGE_NAME`` in the following example with
whatever the actual image name is that is provided. (This would be everything
after ``candidate-registry.fedoraproject.org``, so using the above example then
``$IMAGE_NAME`` would be ``f26/foo:0.1-1.f26container``.)

::

    $ sudo skopeo copy \
        --src-cert-dir /etc/docker/certs.d/candidate-registry.fedoraproject.org/ \
        --dest-cert-dir /etc/docker/certs.d/registry.fedoraproject.org/ \
        docker://candidate-registry.fedoraproject.org/$IMAGE_NAME \
        docker://registry.fedoraproject.org/$IMAGE_NAME

Verification
============

In order to verify, we need to inspect the stable registry, again with `skopeo`_
to ensure the image metadata exists.

::

    $ skopeo inspect docker://registry.fedoraproject.org/$IMAGE_NAME

In this JSON output you will see a list element titled ``RepoTags`` and in there
should be the ``$VERSION-$RELEASE`` listed there, following our example above
this entry would be ``0.1-1.f26container``.

.. _skopeo: https://github.com/projectatomic/skopeo
.. _FAS: https://admin.fedoraproject.org/accounts/
.. _Fedora Layered Image Build System:
    https://docs.pagure.org/releng/layered_image_build_service.html
