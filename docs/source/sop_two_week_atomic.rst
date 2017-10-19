.. SPDX-License-Identifier:    CC-BY-SA-3.0


=====================================
Two Week Atomic Host Release
=====================================

Description
===========

Every two weeks there is a new release of the `Fedora Atomic Host`_ deliverable
from Fedora. This item was originally lead by the `Fedora Cloud SIG`_ and
proprosed as a `Fedora Change`_. The goal is to deliver Fedora Atomic Host at a
more rapid release cycle than that of the rest of Fedora, allowing for the
Atomic Host to be iterated as a released artifact through out a stable Fedora
Release life cycle.

Action
======

There is a script in the `Fedora Releng repo`_ named ``push-two-week-atomic.py``
under the ``scripts/`` directory.

This script must be run from the bodhi backend host, at the time of this writing
that host is ``bodhi-backend01.phx2.fedoraproject.org``.

.. note::
    The user that runs this must also have permissions in `sigul`_ to sign using
    the specified key.

Running the script requires two arguements:

* The Fedora Release number that you are going to release, example: ``-r 26``
* The Fedora key to sign the checksum metadata files with, example: ``-k
  fedora-26``

At the time of this writing, the `AutoCloud`_ tests are no longer reliable and
are effectively abandoned by those responsible. As such, on Atomic Host Two-Week
Release Day a member of the `Fedora Atomic WG`_ (normally ``dustymabe``) will
email RelEng with the release candidate that should be released.

The email should contain two key pieces of information, the ostree commit hash
and the Compose ID. They should be similar to the following.

::

    d518b37c348eb814093249f035ae852e7723840521b4bcb4a271a80b5988c44a
    Fedora-Atomic-26-20171016.0


As a side effect of the current state of testing, the release script used below
will sometimes display in it's "latest Release Candidate" Compose ID as
something newer than what is reported above by the `Fedora Atomic WG`_ as is
displayed in the example below.

.. note:: The script will prompt you to provide the ostree commit hash provided
          above but we are first ensuring the Commit ID matches.

The below example shows how to perform the Two Week Atomic Release. However, in
this example we are showing that the Compose ID is mismatched. If they are not
mismatched, you can simply carry on following the prompts.

::

    localhost$ ssh bodhi-backend01.phx2.fedoraproject.org

    # If you do not already have the releng repo cloned, do so
    bodhi-backend01$ git clone https://pagure.io/releng.git ~/releng

    # If you do have the releng repo already cloned, make sure to pull the
    # latest
    bodhi-backend01$ cd ~/releng
    bodhi-backend01$ git pull

    # Perform the two week release
    bodhi-backend01$ cd ~/releng/scripts

    # Here we specify the signing key 'fedora-26' and are targeting the Fedora
    # Release '26'
    $  ./push-two-week-atomic.py -k fedora-26 -r 26
    INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): pagure.io
    INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): pagure.io
    INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): pagure.io
    INFO:push-two-week-atomic.py:Checking for masher lock files
    INFO:push-two-week-atomic.py:Checking to make sure release is not currently blocked
    INFO:push-two-week-atomic.py:Querying datagrepper for latest AutoCloud successful tests
    INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): apps.fedoraproject.org
    INFO:push-two-week-atomic.py:TESTED_AUTOCLOUD_INFO
    {
      "atomic_qcow2": {
        "release": "26",
        "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-26-20171017.0/CloudImages/x86_64/images/Fedora-Atomic-26-20171017.0.x86_64.qcow2",
        "name": "Fedora-Atomic-26-20171017.0.",
        "compose_id": "Fedora-Atomic-26-20171017.0",
        "image_name": "Fedora-Atomic-26-20171017.0.x86_64.qcow2"
      },
      "atomic_vagrant_libvirt": {
        "release": "26",
        "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-26-20171017.0/CloudImages/x86_64/images/Fedora-Atomic-Vagrant-26-20171017.0.x86_64.vagrant-libvirt.box",
        "name": "Fedora-Atomic-Vagrant-26-20171017.0.",
        "compose_id": "Fedora-Atomic-26-20171017.0",
        "image_name": "Fedora-Atomic-Vagrant-26-20171017.0.x86_64.vagrant-libvirt.box"
      },
      "atomic_raw": {
        "release": "26",
        "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-26-20171017.0/CloudImages/x86_64/images/Fedora-Atomic-26-20171017.0.x86_64.raw.xz",
        "name": "Fedora-Atomic-26-20171017.0.",
        "compose_id": "Fedora-Atomic-26-20171017.0",
        "image_name": "Fedora-Atomic-26-20171017.0.x86_64.raw.xz"
      },
      "atomic_vagrant_virtualbox": {
        "release": "26",
        "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-26-20171017.0/CloudImages/x86_64/images/Fedora-Atomic-Vagrant-26-20171017.0.x86_64.vagrant-virtualbox.box",
        "name": "Fedora-Atomic-Vagrant-26-20171017.0.",
        "compose_id": "Fedora-Atomic-26-20171017.0",
        "image_name": "Fedora-Atomic-Vagrant-26-20171017.0.x86_64.vagrant-virtualbox.box"
      }
    }
    INFO:push-two-week-atomic.py:Query to datagrepper complete
    INFO:push-two-week-atomic.py:Extracting compose_id from tested autocloud data
    Releasing compose Fedora-Atomic-26-20171017.0
    Tree commit:

In this instance we can see that the line ``Release compose
Fedora-Atomic-26-20171017.0`` is a day newer in date-stamp than the one provided
in the example information above as it would come from the Atomic WG. Therefore
a member of RelEng needs to clone the `mark-atomic-bad`_ git repository and add
``Fedora-Atomic-26-20171017.0`` to the ``bad-composes.json`` file to effectively
"lie" to the script.

.. note:: This is a work-around that was supposed to be replaced by a fully
          automated release workflow but the tests never became truly
          authoritative so the temporary fix became standard practice. Once this
          is no longer the case, this document should be updated to reflect the
          new process.

.. note:: In the event the next Two-Week Release window comes around and the
          image needing to be released is the one you had to mark in
          ``bad-composes.json`` something has seriously gone wrong. This
          situation realistically should never occur. However, if it did occur
          and there's a valid reason for it and you **really** want to do that
          then you can just remove that Compose ID from the
          ``bad-composes.json`` file.

::

    # We need to clone the repo
    $ git clone ssh://git@pagure.io/mark-atomic-bad.git

    # Edit the bad-composes.json file to contain Fedora-Atomic-26-20171017.0 in
    # the json list called "bad-composes"
    # NOTE THAT JSON SYNTAX DOES NOT ALLOW A TRAILING COMMA

    # Now commit the change
    $ git add bad-composes.json
    $ git commit -m "mark Fedora-Atomic-26-20171017.0 to ensure Fedora-Atomic-26-20171016.0 is latest"
    $ git push origin master

Now re-run the ``push-two-week-atomic.py`` script as described above.

Verification
============

In order to verify this change has taken place, you should see emails on the
various mailing lists that are defined in the list ``ATOMIC_EMAIL_RECIPIENTS``
in the ``push-two-week-atomic.py`` script. At the time of this writing, those
are:

::

    ATOMIC_EMAIL_RECIPIENTS = [
        "cloud@lists.fedoraproject.org",
        "rel-eng@lists.fedoraproject.org",
        "atomic-devel@projectatomic.io",
        "atomic-announce@projectatomic.io",
    ]

This can also be verified by checking that the appropriate `fedmsg`_ messages
were sent and recently received by `Datagrepper`_ in `this datagrepper query`_.

One final item to check is that the actual compose artifacts have made their way
into the `appropriate stable directories`_.

.. _sigul: https://pagure.io/sigul
.. _fedmsg: http://www.fedmsg.com/en/latest/
.. _Datagrepper: https://apps.fedoraproject.org/datagrepper/
.. _Fedora RelEng repo: https://pagure.io/releng
.. _Fedora Cloud SIG: https://fedoraproject.org/wiki/Cloud_SIG
.. _Fedora Atomic WG: https://pagure.io/atomic-wg
.. _Fedora Change: https://fedoraproject.org/wiki/Changes/Two_Week_Atomic
.. _Fedora Atomic Host: https://getfedora.org/en/cloud/download/atomic.html
.. _appropriate stable directories:
        http://alt.fedoraproject.org/pub/alt/atomic/stable/
.. _this datagrepper query:
    https://apps.fedoraproject.org/datagrepper/raw?category=releng&delta=127800
.. _AutoCloud: https://apps.fedoraproject.org/autocloud/compose
.. _mark-atomic-bad: https://pagure.io/mark-atomic-bad
