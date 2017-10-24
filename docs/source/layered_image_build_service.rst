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
    [ Every time an image is tagged or changes names, Robosignatory signs it ]
    [                                                                        ]
    [ NOTE: It's injection points in the diagram are ommitted for brevity    ]
    [------------------------------------------------------------------------]


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

* Taskotron
* fedmsg
* RelEng Automation


The build system is setup such that Fedora Layered Image maintainers will submit
a build to Koji via the ``fedpkg container-build`` command a ``containers``
namespace within `DistGit`_. This will trigger the build to be scheduled in
`OpenShift`_ via `osbs-client`_ tooling, this will create a custom
`OpenShift Build`_ which will use the pre-made buildroot Docker image that we
have created. The `Atomic Reactor`_ (``atomic-reactor``) utility will run within
the buildroot and prep the build container where the actual build action will
execute, it will also maintain uploading the `Content Generator`_ metadata back
to `Koji`_ and upload the built image to the candidate docker registry. This
will run on a host with iptables rules restricting access to the docker bridge,
this is how we will further limit the access of the buildroot to the outside
world verifying that all sources of information come from Fedora.

Completed layered image builds are hosted in a candidate docker registry which
is then used to pull the image and perform tests with `Taskotron`_. The
taskotron tests are triggered by a `fedmsg`_ message that is emitted from
`Koji`_ once the build is complete. Once the test is complete, taskotron will
send fedmsg which is then caught by the `RelEng Automation` Engine that will run
the Automatic Release tasks in order to push the layered image into a stable
docker registry in the production space for end users to consume.

Note that every time the layered image tagged to a new registry, ultimately
changing it's name, `Robosignatory`_ will automatically sign the new image. This
will also occur as part of the Automated Release process as the image will be
tagged from the candidate docker registry into the production docker registry in
order to "graduate" the image to stable.

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

Fedora Production Registry
~~~~~~~~~~~~~~~~~~~~~~~~~~

Implementation details of this are still unknown at the time of this writing and
will be updated at a later date. For the current status and implementation notes
please visit the `FedoraDockerRegistry`_ page.

Taskotron
---------

`Taskotron`_ is an automated task execution framework, written on top of
`buildbot`_ that currently executes many Fedora automated QA tasks and we will
be adding the Layered Image automated QA tasks. The tests themselves will be
held in DistGit and maintained by the Layered Image maintainers.

RelEng Automation
-----------------

`RelEng Automation`_ is an ongoing effort to automate as much of the RelEng
process as possible by using `Ansible`_ and being driven by `fedmsg`_ via
`Loopabull`_ to execute Ansible Playbooks based on fedmsg events.

Robosignatory
-------------

`Robosignatory`_ is a fedmsg consumer that automatically signs artifacts and
will be used to automatically sign docker layered images for verification by
client tools as well as end users.

Future Integrations
-------------------

In the future various other components of the `Fedora Infrastructure`_
will likely be incorporated.

PDC
~~~

`PDC`_ is Fedora's implementation of `Product Definition Center`_ which allows
Fedora to maintain a database of each Compose and all of it's contents in a way
that can be queried and used to make decisions in a programatic way.

The New Hotness
~~~~~~~~~~~~~~~

`The New Hotness`_ is a `fedmsg`_ consumer that listens to
release-monitoring.org and files bugzilla bugs in response (to notify packagers
that they can update their packages).

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
