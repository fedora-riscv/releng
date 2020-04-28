.. SPDX-License-Identifier:    CC-BY-SA-3.0


=======================================
Release the Fedora Container Base Image
=======================================

Description
===========

This SOP covers the steps involved in changing and releasing the Fedora Container
Base image.

Fedora releases 2 container base images, `fedora` and `fedora-minimal`. These images
are available on 3 registries `registry.fedoraproject.org`, `quay.io` and `DockerHub` (fedora-minimal is not available in DockerHub).


Modify a base image (Kickstart)
-------------------------------

Base images are built in koji using the `image-factory` application to build the container
image root filesystem (rootfs).
Kickstart files are used to configure how the image is built and what is available in the image
The solution consist of 3 Kickstarts.

`fedora-container-common <https://pagure.io/fedora-kickstarts/blob/master/f/fedora-container-common.ks>`_

`fedora-container-base <https://pagure.io/fedora-kickstarts/blob/master/f/fedora-container-base.ks>`_

`fedora-container-base-minimal <https://pagure.io/fedora-kickstarts/blob/master/f/fedora-container-base-minimal.ks>`_

Changes made on the master branch will results in the rawhide image, other branches (f30, f31) should
be used to modify other releases.

Compose Configuration (Pungi)
-----------------------------

The configuration used to compose the container images is available in the pungi-fedora repository.

For rawhide the configuration is in

https://pagure.io/pungi-fedora/blob/master/f/fedora.conf

While for other releases the configuration is in a dedicated file

https://pagure.io/pungi-fedora/blob/f31/f/fedora-container.conf


Release on registry.fedoraproject.org and quay.io
-------------------------------------------------

If you want to release the base image on registry.fp.o and quay.io you can use the following
script.

`sync-latest-container-base-image.sh <https://pagure.io/releng/blob/master/f/scripts/sync-latest-container-base-image.sh>`_

You will need to run that script from on of the releng composer machines in the infrastructure
in order to have the credentials.

If you do not have access to that machines, you can request the release by opening a ticket on the `releng tracker <https://pagure.io/releng/issues>`_.

The script can then be executed as follow

::

    $./sync-latest-container-base-image.sh 31
    $./sync-latest-container-base-image.sh 32

This will take care of pushing the `fedora` and `fedora-minimal` images to both registries.



Release on DockerHub
--------------------

Releasing on DockerHub is a little different since Fedora is an "offical" image there. In order to
release new images there we have to update a Dockerfile and rootfs tarball on the following repo.

`docker-brew-fedora <https://github.com/fedora-cloud/docker-brew-fedora>`_.

For the details on how to run the script please see

`README <https://github.com/fedora-cloud/docker-brew-fedora/blob/master/README.md>`_.
