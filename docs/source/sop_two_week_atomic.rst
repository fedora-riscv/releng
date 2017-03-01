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

* The Fedora Release number that you are going to release, example: ``-r 23``
* The Fedora key to sign the checksum metadata files with, example: ``-k
  fedora-23``

.. note::
    Before running this script, make sure that the previous compose was
    successful by verifying that the ``Cloud-Images/x86_64/Images/`` directory
    is populated under the compose directory:
    http://alt.fedoraproject.org/pub/alt/atomic/testing/

    This should not always be necessary, but while the compose work is being
    iterated on it's recommended.

The below example shows how to perform the Two Week Atomic Release.

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
    bodhi-backend01$ ./push-two-week-atomic.py -r 23 -k fedora-23

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
.. _Fedora Change: https://fedoraproject.org/wiki/Changes/Two_Week_Atomic
.. _Fedora Atomic Host: https://getfedora.org/en/cloud/download/atomic.html
.. _appropriate stable directories:
        http://alt.fedoraproject.org/pub/alt/atomic/stable/
.. _this datagrepper query:
    https://apps.fedoraproject.org/datagrepper/raw?category=releng&delta=127800
