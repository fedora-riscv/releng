.. SPDX-License-Identifier:    CC-BY-SA-3.0


===============
Pushing Updates
===============

Description
===========

Fedora updates are typically pushed once a day. This SOP covers the steps
involved.

Coordinate
----------

Releng has a rotation of who pushes updates when. Please coordinate and only
push updates when you are expected to or have notified other releng folks you
are doing so. See: https://apps.fedoraproject.org/calendar/release-engineering/
for the list or on irc you can run ``.pushduty`` in any channel with zodbot to
see who is on duty this week.

Login to machine to sign updates
--------------------------------

Login to a machine that is configured for sigul client support and has the
bodhi client installed. Currently, this machine is:
``bodhi-backend01.phx2.fedoraproject.org``

Decide what releases you're going to push.
------------------------------------------

* If there is a Freeze ongoing, you SHOULD NOT push all stable requests for a
  branched release, only specific blocker or freeze exception requests that QA
  will request in a releng ticket.

* If there is no Freeze ongoing you can push all Fedora and EPEL releases at
  the same time if you wish.

* From time to time there may be urgent requests in some branches, you can only
  push those if requested. Note however that bodhi2 will automatically push
  branches with security updates before others.

Get a list of packages to push
------------------------------

::

    $ sudo -u apache bodhi-push --releases 'f26,f25,f24,epel-7,EL-6' --username <yourusername>
    <enter your password+2factorauth, then your fas password>

Sometimes you see a warning "Warning: foobar-1.fcxx has unsigned builds and has been skipped"
which means those updates are currently getting signed and it can verified by listing the
tagged builds in fxx-signing-pending tag.

::
    $ koji list-tagged fxx-signing-pending

You can say 'n' to the push at this point if you wish to sign packages (see
below). Or you can keep this request open in a window while you sign the
packages, then come back and say y.

List the releases above you wish to push from: 25 24 5 6 7, etc

You can also specify ``--request=testing`` to limit pushes. Valid types are
``testing`` or ``stable``.

The list of updates should be in the cache directory named ``Stable-$Branch``
or ``Testing-$Branch`` for each of the Branches you wished to push.

During freezes you will need to do two steps: (If say, fedora 26 branched was
frozen):

::

    $ sudo -u apache bodhi-push --releases f26 --request=testing \
        --username <username>

Then

::

    $ sudo -u apache bodhi-push --releases 'f25,f24,epel-7,EL-6' --username <username>

During the Release Candidate compose phase we tag builds to be included into a
-compose tag (e.g. f26-compose). When we have a candidate that has been signed off as gold
we need to ensure that all builds tagged into the -compose tag have been pushed stable.
Once we have pushed all -compose builds stable we then have to clone the base tag (e.g. f26)
to a tag for the milestone for Alpha and Beta (e.g. f26-Alpha). After final release we need
to lock the base tag and adjust the release status in bodhi so that updates now hit the
-updates tag (e.g. f26-updates). Once we have cloned the tag or locked the tag and adjusted
bodhi we are free to push stable updates again.

Pushing Stable updates during freeze
------------------------------------

During feezes we need to push to stable builds included in the compose.  QA
will file a ticket with the nvrs to push.

.. note::

    If you are pushing a bodhi update that contains multiple builds, you need
    only pass bodhi-push a single build nvr and all the others in that update
    will be detected and pushed along with it. However, if you are pushing
    multiple disjoint bodhi updates then each build will need to be listed
    individually.

::

    $ sudo -u apache bodhi-push --builds '<nvr1>,<nvr2>,...' --username <username>


There are no updates to push.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you are getting the message ``There are no updates to push.`` or the list of
packages you are seeing to push out for the Stable updates request is not
correct compared to what you specified in the ``--builds`` section of the
command above then one of two things likely happened.

#. The update hasn't yet reached appropriate karma

   This should be handled case-by-case, if the QA Team has requested this be
   pushed as stable to fix a blocker but there's not yet enough karma for an
   autostable prompt to occur then you should verify with QA that these are
   ready to go out even without karma. If they are, then log into the Bodhi
   WebUI and modify the karma threshold of the update to 1 and add karma (if
   necessary). This is not something we should do as normal practice and is
   considered an edge case. When update requests come to RelEng, it should have
   appropriate karma. Sometimes it doesn't and as long as QA approves, we need
   not block on it.

#. The update was never requested for stable

   It's possible the update wasn't requested for stable, you can resolve this by
   running the following on one of the bodhi-backend systems:

   ::

    bodhi updates request <BODHI-REQUEST-ID> stable



Perform the bodhi push
----------------------

Say 'y' to push for the above command.

Verification
============
#. Monitor Bodhi's composes with ``bodhi-monitor-composes``

   ::

    $ sudo -u apache watch -d -n 60 bodhi-monitor-composes

#. Monitor the systemd journal

   ::

    $ sudo journalctl -o short -u fedmsg-hub -l -f

#. Check the processes

   ::

    $ ps axf|grep bodhi

#. Watch for fedmsgs through the process. It will indicate what releases it's
   working on, etc. You may want to watch in ``#fedora-fedmsg``.

   ::

        bodhi.masher.start -- kevin requested a mash of 48 updates
        bodhi.mashtask.start -- bodhi masher started a push
        bodhi.mashtask.mashing -- bodhi masher started mashing f23-updates
        bodhi.mashtask.mashing -- bodhi masher started mashing f22-updates-testing
        ...
        bodhi.update.complete.stable -- moceap's wondershaper-1.2.1-5.fc23 bodhi update completed push to stable https://admin.fedoraproject.org/updates/FEDORA-2015-13052
        ...
        bodhi.errata.publish -- Fedora 23 Update: wondershaper-1.2.1-5.fc23 https://admin.fedoraproject.org/updates/FEDORA-2015-13052
        bodhi.mashtask.complete -- bodhi masher successfully mashed f23-updates
        bodhi.mashtask.sync.wait -- bodhi masher is waiting for f22-updates-testing to hit the master mirror

#. Seach for problems with a particular push:

   ::

        sudo journalctl --since=yesterday -o short -u fedmsg-hub | grep dist-6E-epel (or f22-updates, etc)

#. Note: Bodhi will look at the things you have told it to push and see if any have security updates, those branches will be started first. It will then fire off threads (up to 3 at a time) and do the rest.

Consider Before Running
=======================
Pushes often fall over due to tagging issues or unsigned packages.  Be
prepared to work through the failures and restart pushes from time to
time

::

    $ sudo -u apache bodhi-push --resume

Bodhi will ask you which push(es) you want to resume.


Common issues / problems with pushes
====================================

* When the push fails due to new unsigned packages that were added after you
  started the process. re-run step 4a or 4b with just the package names that
  need to be signed, then resume.

* When the push fails due to an old package that has no signature, run:
  ``koji write-signed-rpm <gpgkeyid> <n-v-r>`` and resume.

* When the push fails due to a package not being tagged with updates-testing
  when being moved stable: ``koji tag-pkg dist-<tag>-updates-testing <n-v-r>``

* When signing fails, you may need to ask that the sigul bridge or server be
  restarted.

* If the updates push fails with a:
  ``OSError: [Errno 16] Device or resource busy: '/var/lib/mock/*-x86_64/root/var/tmp/rpm-ostree.*'``
  You need to umount any tmpfs mounts still open on the backend and resume the push.

* If the updates push fails with:
  ``"OSError: [Errno 39] Directory not empty: '/mnt/koji/mash/updates/*/../*.repocache/repodata/'``
  you need to restart fedmsg-hub on the backend and resume.

* If the updates push fails with:
  ``IOError: Cannot open /mnt/koji/mash/updates/epel7-160228.1356/../epel7.repocache/repodata/repomd.xml: File /mnt/koji/mash/updates/epel7-160228.1356/../epel7.repocache/repodata/repomd.xml doesn't exists or not a regular file``
  This issue will be resolved with NFSv4, but in the mean time it can be worked around by removing the `.repocache` directory and resuming the push.
  ``$ sudo rm -fr /mnt/koji/mash/updates/epel7.repocache``

* If the Atomic OSTree compose fails with some sort of `Device or Resource busy` error, then run `mount` to see if there are any stray `tmpfs` mounts still active:
  ``tmpfs on /var/lib/mock/fedora-22-updates-testing-x86_64/root/var/tmp/rpm-ostree.bylgUq type tmpfs (rw,relatime,seclabel,mode=755)``
  You can then
  ``$ sudo umount /var/lib/mock/fedora-22-updates-testing-x86_64/root/var/tmp/rpm-ostree.bylgUq`` and resume the push.

Other issues should be addressed by releng or bodhi developers in
``#fedora-releng``.


