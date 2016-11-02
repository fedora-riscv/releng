.. SPDX-License-Identifier:    CC-BY-SA-3.0


================================================
Fedora Release Engineering Troubleshooting Guide
================================================

Fedora Release Engineering consists of many different systems, many different
code bases and multiple tools. Needless to say, things can get pretty complex
in a hurry. This aspect of Fedora Release Engineering is not very welcoming to
newcomers who would like to get involved. This guide stands as a place to
educate those new to the processes, systems, code bases, and tools. It also is
to serve as a reference to those who aren't new but maybe are fortunate enough
to not have needed to diagnose things in recent memory.

We certainly won't be able to document every single possible compontent in the
systems that could go wrong but hopefully over time this document will stand as
a proper knowledge base for reference and educational purposes on the topics
listed below.

Compose
=======

If something with a compose has gone wrong, there's a number of places to find
information. Each of these are discussed below.

releng-cron list
----------------

The compose output logs are emailed to the releng-cron mailing list. It is
good practice to check the `releng-cron mailing list archives`_ and find the
latest output and give it a look.

.. _compose-machines:

compose machines
----------------

If the `releng-cron mailing list archives`_ doesn't prove to be useful, you can
move on to checking the contents of the composes themselves on the primary
compose machines in the Fedora Infrastructure. At the time of this writing,
there are multiple machines based on the specific compose you are looking for:

* Two-Week Atomic Nightly Compose

  * ``compose-x86-01.phx2.fedoraproject.org``

* Branched Compose

  * ``branched-composer.phx2.fedoraproject.org``

* Rawhide Compose

  * ``rawhide-composer.phx2.fedoraproject.org``

Depending on which specific compose you are in search of will depend on what
full path you will end up inspecting:

* For Two Week Atomic you will find the compose output in
  ``/mnt/fedora_koji/compose/``
* For Release Candidate / Test Candidate composes you will find compose output
  in ``/mnt/koji/compose/``

.. note::
    It's possible the mock logs are no longer available. The mock chroots are
    rewritten on subsequent compose runs.

You can also check for mock logs if they are still persisting from the compose
you are interested in. Find the specific mock chroot directory name (that will
reside in ``/var/lib/mock/``) you are looking for by checking the appropriate
compose mock configuration (the following is only a sample provided at the time
of this writing):

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

running the compose yourself
----------------------------

If you happen to strike out there and are still in need of debugging, it might
be time to just go ahead and run the compose yourself. The exact command needed
can be found in the cron jobs located on their respective compose machines, this
information can be found in the :ref:`compose-machines` section. Also note that
each respective compose command should be ran from it's respective compose
machine as outlined in the :ref:`compose-machines` section.

An example is below, setting the compose directory as your ``username-debug.1``,
the ``.1`` at the end is common notation for an incremental run of a compose. If
you need to do another, increment it to ``.2`` and continue. This is helpful to
be able to compare composes.

.. note::
    It is recommended that the following command be run in `screen`_ or `tmux`_

::

    $ TMPDIR=`mktemp -d /tmp/twoweek.XXXXXX` && cd $TMPDIR \
        && git clone -n https://pagure.io/releng.git && cd releng && \
        git checkout -b stable twoweek-stable && \
        LANG=en_US.UTF-8 ./scripts/make-updates 23 updates $USER-debug.1

The above command was pulled from the ``twoweek-atomic`` cron job with only the
final parameter being altered. This is used as the name of the output directory.

The compose can take some time to run, so don't be alarmed if you don't see
output in a while. This should provide you all the infromation needed to debug
and/or diagnose further. When in doubt, as in ``#fedora-releng`` on
``irc.freenode.net``.

Docker Layered Image Build Service
==================================

The `Docker Layered Image Build Service`_ is built using a combination of
technologies such as `OpenShift`_, `osbs-client`_, and the
`koji-containerbuild`_ plugin that when combined are often refered to as an
OpenShift Build Service instance (OSBS). Something to note is that `OpenShift`_
is a `kubernetes`_ distribution with many features built on top of `kubernetes`_
such as the `build primitive`_ that is used as the basis for the build service.
This information will hopefully shed light on some of the terminology and
commands used below.

There are a few "common" scenarios in which build may fail or hang that will
need some sort of inspection of the build system.

Build Appears to stall after being scheduled
--------------------------------------------

In the event that a build scheduled through koji appears to be stalled and is
not in a ``free`` state (i.e. - has been scheduled). An administrator will need
to ssh into ``osbs-master01`` or ``osbs-master01.stg`` (depending stage vs
production) and inspect the build itself.

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

The information found in the commands above will generally identify the issue.

Build fails but there's no log output in the Koji Task
------------------------------------------------------

Sometimes there is a communications issue between Koji and OSBS which cause for
a failure to be listed in Koji but without all the logs. These can be diagnosed
by checking the ``kojid`` logs on the Koji builder listed in the task output.

For example:

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

In this example the buildContiner task was scheduled and ran on
``buildvm-04.stg`` with the actual createContainer task being on
``buildvm-02.stg``, and ``buildvm-02.stg`` is where we're going to want to begin
looking for failures to communicate with OSBS as this is the point of contact
with the external system.

Logs can be found in ``/var/log/kojid.log`` or if necessary, check the koji hub
in question. Generally, you will want to start with the first point of contact
with OSBS and "work your way back" so in the above example you would first check
``buildvm-02.stg``, then move on to ``buildvm-04.stg`` if nothing useful was
found in the logs of the previous machine, and again move on to the koji hub if
neither of the builder machines involved provided useful log information.

Build fails because it can't get to a network resource
------------------------------------------------------

Sometimes there is a situation where the firewall rules get messed up on one of
the OpenShift Nodes in the environment. This can cause output similar to the
following:

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


If we go to the OSBS Master and run the following commands, we will see the root
symptom:

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


In the above output, we can see that we do actually have network connectivity to
the Node but we can not connect to the OpenShift service that should be
listening on port ``10250``.

To fix this, you need to ssh into the OpenShift Node that you can't connect to
via port ``10250`` and run the following commands. This should resolve the
issue.

::

    iptables -F && iptables -t nat -F && systemctl restart docker && systemctl restart origin-node

.. _tmux: https://tmux.github.io/
.. _kubernetes: http://kubernetes.io/
.. _OpenShift: https://www.openshift.org/
.. _screen: https://www.gnu.org/software/screen/
.. _osbs-client: https://github.com/projectatomic/osbs-client
.. _build primitive: https://docs.openshift.org/latest/dev_guide/builds.html
.. _koji-containerbuild:
    https://github.com/release-engineering/koji-containerbuild
.. _releng-cron mailing list archives:
    https://lists.fedoraproject.org/archives/list/releng-cron@lists.fedoraproject.org/
.. _Docker Layered Image Build Service:
    https://fedoraproject.org/wiki/Changes/Layered_Docker_Image_Build_Service
