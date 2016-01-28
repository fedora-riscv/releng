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

.. _tmux: https://tmux.github.io/
.. _screen: https://www.gnu.org/software/screen/
.. _releng-cron mailing list archives:
    https://lists.fedoraproject.org/archives/list/releng-cron@lists.fedoraproject.org/
