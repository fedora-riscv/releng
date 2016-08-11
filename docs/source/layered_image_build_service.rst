.. SPDX-License-Identifier:    CC-BY-SA-3.0

=================================
Fedora Layered Image Build System
=================================

The Fedora Layered Image Build System aims to provide an new type of official
binary artifact produced by Fedora. Currently, we produce two main types of
artifacts: RPMs, and images. The RPMs are created in `Koji`_ from specfiles in
dist-git. The images come in different formats, but have in common creation in
Koji from kickstart files — this includes the official Fedora Docker Base Image.
This change introduces a new type of image, a `Docker`_ Layered Image, which is
created from a Dockerfile and builds on top of that base image.


Layered Image Build Service Architecture
========================================

::

    +------------------------------+
    | Future Items to Integrate    |
    +------------------------------+
    | +--------------------------+ |
    | |PDC Integration           | |
    | +--------------------------+ |
    | |Taskotron                 | |
    | +--------------------------+ |
    | |fedmsg   Handlers         | |
    | +--------------------------+ |
    | |Other???                  | |
    | +--------------------------+ |
    |  Magical Future CI/AutoTest  |
    |                              |
    +------------------------------+

                                            +----------------+
                                            |  Fedora        |
                                            |  Layered Image |
                                            |  Maintainers   |
                                            |                |
                                            |                |
                                            +-------+--------+
                                                    |
                                                    V
                                            +-------+--------------+
                                            |                      |
                                            | +------------------+ |
                                            | |Dockerfile        | |
                                            | +------------------+ |
                                            | |App "init" scripts| |
                                            | +------------------+ |
                                            | |Docs              | |
                                            | +------------------+ |
                                            |  DistGit             |
                                            |                      |
                                            +-----------+----------+
           +------------------+                         |
           |Fedora            |                         |
           |Users/Contributors|                         |
           +--------+---------+                         |
                    ^                                   |
                    |                                   |
                    |                                   |
                    |                                   |
                    |                                   |
    +---------------+-----------+                       |
    |                           |                       |
    | +----------------------+  |                       +---------------+
    | |Intermediate Docker   |  |                                       |
    | |Images for OSBS Builds|  |                                       |
    | +----------------------+  |        +--------------------------+   |
    | |Layered Images        |  |        |                          |   |
    | +----------------------+  |        | +----------------------+ |   |
    | |Pulp/Pulp|Crane       |  |        | |containerbuild plugin | |   |
    | +----------------------+  |        | +----------------------+ |   |
    | |docker|distribution   |  |        | |rpmbuilds             | |   |
    | +----------------------+  |        | +----------------------+ |   |
    |  Registry                 |        |  koji                    |   |
    |                           |        |                          |   |
    +-----+----+----------------+        +-----+---+----+-----------+   |
          |    ^                               |   ^    ^               |
          |    |                               |   |    |               |
          |    |   +---------------------------+   |    |               |
          |    |   |                               |    |               |
          |    |   |   +---------------------------+    |               |
          |    |   |   |                                |               |
          |    |   |   |                                |               |
          V    |   V   |                                |               |
       +--+----+---+---+---+                            |               |
       |                   |             +--------------+--------+      |
       | +--------------+  |             |fedpkg container build +<-----+
       | |OpenShift v3  |  |             +-----------------------+
       | +--------------+  |
       | |Atomic Reactor|  |
       | +--------------+  |
       |  OSBS             |
       |                   |
       +-------------------+


Layered Image Build System Components
=====================================

The main aspects of the Layered Image Build System are:

* Koji

  * koji-containerbuild plugin

* OpenShift Origin v3
* Atomic Reactor
* osbs-client tools
* A docker registry

  * docker-distribution


The build system is setup such that Fedora Layered Image maintainers will submit
a build to Koji via the ``fedpkg container-build`` command a ``docker``
namespace within `DistGit`_. This will trigger the build to be scheduled in
`OpenShift`_ via `osbs-client`_ tooling, this will create a custom
`OpenShift Build`_ which will use the pre-made buildroot Docker image that we
have created. The `atomic-reactor`_ utility will run within the buildroot and
prep the build container where the actual build action will execute, it will
also maintain uploading the `Content Generator`_ metadata back to `Koji`_ and
upload the built image to the candidate docker registry. This will run on a
host with iptables rules restricting access to the docker bridge, this is how we
will further limit the access of the buildroot to the outside world verifying
that all sources of information come from Fedora.

Koji
----

`Koji`_ is the Fedora Build System.


koji-containerbuild plugin
--------------------------

The `koji-containerbuild`_ plugin integrates Koji and OSBS so that builds can be
scheduled by koji and integrated into the build system with imports of metadata,
logs, build data, and build artifacts.

OpenShift Origin v3
-------------------

`OpenShift Origin v3`_ is an open source Container Platform, built on top of
`kubernetes`_ and `Docker`_. This provides many aspects of the system needed
including a build pipeline for Docker images with custom build profiles, image
streams, and triggers based on events within the system.

Atomic Reactor
--------------

`Atomic Reactor`_ is an utility which allows for the building of containers from
within other containers providing hooks to trigger automation of builds as well
as plugins providing automatic integration many other utilities and services.


osbs-client tools
-----------------

`osbs-client`_ tools allow for users to access the build functionality of
`OpenShift Origin v3`_ using a simple set of command line utilities.


docker-registry
---------------

A `docker-registry`_ is a stateless, highly scalable server side application
that stores and lets you distribute Docker images.

There are many different implementations of docker-registries, two main ones
are supported by the Fedora Layered Image Build System.

docker-distribution
~~~~~~~~~~~~~~~~~~~

The `docker-distribution`_ registry is considered the Docker upstream "v2
registry" such that it was used by upstream to implement the new version 2
specification of the docker-registry.

pulp-crane
~~~~~~~~~~

.. note:: At this time Pulp/Crane is still future work as part of the `Fedora
          Docker Registry`_ Change.

Crane, `pulp-crane`_, is a small read-only web application that provides enough
of the docker registry API to support "docker pull". Crane does not serve the
actual image files, but instead serves 302 redirects to some other location
where files are being served. A base file location URL can be specified
per-repository.

This functionality allows for the Crane endpoint to be used as the entry into
the `Fedora Mirror Network`_.




.. _kubernetes: http://kubernetes.io/
.. _Koji: https://fedoraproject.org/wiki/Koji
.. _Docker: https://github.com/docker/docker/
.. _pulp-crane: https://github.com/pulp/crane
.. _OpenShift: https://www.openshift.org/
.. _OpenShift Origin V3: https://www.openshift.org/
.. _docker-registry: https://docs.docker.com/registry/
.. _osbs-client: https://github.com/projectatomic/osbs-client
.. _docker-distribution: https://github.com/docker/distribution/
.. _Atomic Reactor: https://github.com/projectatomic/atomic-reactor
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
