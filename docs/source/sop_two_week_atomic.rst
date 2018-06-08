.. SPDX-License-Identifier:    CC-BY-SA-3.0


=====================================
Two Week Atomic Host Release
=====================================

Description
===========

Every two weeks there is a new release of the `Fedora Atomic Host`_ deliverable
from Fedora. This item was originally lead by the `Fedora Cloud SIG`_ and
proposed as a `Fedora Change`_. The goal is to deliver Fedora Atomic Host at a
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

Running the script requires two arguments:

* The Fedora Release number that you are going to release, example: ``-r 28``
* The Fedora key to sign the checksum metadata files with, example: ``-k
  fedora-28``

At the time of this writing, the `AutoCloud`_ tests are no longer reliable and
are effectively abandoned by those responsible. We have also stopped relying on
autocloud fedmsg for getting image details. Instead, we are using `fedfind`_
which gives us image details for all supported architectures.
As such, on Atomic Host Two-Week
Release Day a member of the `Fedora Atomic WG`_ (normally ``dustymabe``) will
open a request to RelEng with the release candidate that should be released.

The request should contain a few key pieces of information. The pungi compose
id of the compose that created the media artifacts and optionally the pungi
compose id of the compose that created the ostrees (only if the media
and the ostree were created in different composes).

::

    pungi-compose-id: Fedora-Atomic-28-20180515.1
    ostree-pungi-compose-id: Fedora-28-updates-20180515.1

Or the request may just contain the full command to run

::

    push-two-week-atomic.py -k fedora-28 -r 28 --pungi-compose-id Fedora-Atomic-28-20180515.1 --ostree-pungi-compose-id Fedora-28-updates-20180515.1


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

    # Here we specify the signing key 'fedora-28' and are targeting the Fedora
    # Release '28' and specific pungi composes
        bodhi-backend01$ python push-two-week-atomic.py -k fedora-28 -r 28 --pungi-compose-id Fedora-Atomic-28-20180515.1 --ostree-pungi-compose-id Fedora-28-updates-20180515.1
        INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): pagure.io
        INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): pagure.io
        INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): pagure.io
        INFO:push-two-week-atomic.py:Fetching images information for Compose ID Fedora-Atomic-28-20180515.1
        INFO:push-two-week-atomic.py:Begin fetching image metadata information using fedfind for Compose ID Fedora-Atomic-28-20180515.1
        INFO:push-two-week-atomic.py:Finished fetching image metadata information using fedfind for Compose ID Fedora-Atomic-28-20180515.1
        INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): apps.fedoraproject.org
        INFO:push-two-week-atomic.py:RELEASE_ARTIFACTS_INFO
        {
          "aarch64": {
            "atomic_dvd_ostree": {
              "name": "Fedora-AtomicHost-ostree-aarch64-28-20180515.1.iso",
              "image_name": "Fedora-AtomicHost-ostree-aarch64-28-20180515.1.iso",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/aarch64/iso/Fedora-AtomicHost-ostree-aarch64-28-20180515.1.iso",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 988649472
            },
            "atomic_qcow2": {
              "name": "Fedora-AtomicHost-28-20180515.1",
              "image_name": "Fedora-AtomicHost-28-20180515.1.aarch64.qcow2",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/aarch64/images/Fedora-AtomicHost-28-20180515.1.aarch64.qcow2",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 621911040
            },
            "atomic_raw": {
              "name": "Fedora-AtomicHost-28-20180515.1",
              "image_name": "Fedora-AtomicHost-28-20180515.1.aarch64.raw.xz",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/aarch64/images/Fedora-AtomicHost-28-20180515.1.aarch64.raw.xz",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 396619232
            }
          },
          "x86_64": {
            "atomic_dvd_ostree": {
              "name": "Fedora-AtomicHost-ostree-x86_64-28-20180515.1.iso",
              "image_name": "Fedora-AtomicHost-ostree-x86_64-28-20180515.1.iso",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/x86_64/iso/Fedora-AtomicHost-ostree-x86_64-28-20180515.1.iso",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 1034944512
            },
            "atomic_qcow2": {
              "name": "Fedora-AtomicHost-28-20180515.1",
              "image_name": "Fedora-AtomicHost-28-20180515.1.x86_64.qcow2",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/x86_64/images/Fedora-AtomicHost-28-20180515.1.x86_64.qcow2",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 635537920
            },
            "atomic_vagrant_libvirt": {
              "name": "Fedora-AtomicHost-Vagrant-28-20180515.1",
              "image_name": "Fedora-AtomicHost-Vagrant-28-20180515.1.x86_64.vagrant-libvirt.box",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/x86_64/images/Fedora-AtomicHost-Vagrant-28-20180515.1.x86_64.vagrant-libvirt.box",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 603786982
            },
            "atomic_raw": {
              "name": "Fedora-AtomicHost-28-20180515.1",
              "image_name": "Fedora-AtomicHost-28-20180515.1.x86_64.raw.xz",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/x86_64/images/Fedora-AtomicHost-28-20180515.1.x86_64.raw.xz",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 457994952
            },
            "atomic_vagrant_virtualbox": {
              "name": "Fedora-AtomicHost-Vagrant-28-20180515.1",
              "image_name": "Fedora-AtomicHost-Vagrant-28-20180515.1.x86_64.vagrant-virtualbox.box",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/x86_64/images/Fedora-AtomicHost-Vagrant-28-20180515.1.x86_64.vagrant-virtualbox.box",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 617984000
            }
          },
          "ppc64le": {
            "atomic_dvd_ostree": {
              "name": "Fedora-AtomicHost-ostree-ppc64le-28-20180515.1.iso",
              "image_name": "Fedora-AtomicHost-ostree-ppc64le-28-20180515.1.iso",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/ppc64le/iso/Fedora-AtomicHost-ostree-ppc64le-28-20180515.1.iso",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 1036103680
            },
            "atomic_qcow2": {
              "name": "Fedora-AtomicHost-28-20180515.1",
              "image_name": "Fedora-AtomicHost-28-20180515.1.ppc64le.qcow2",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/ppc64le/images/Fedora-AtomicHost-28-20180515.1.ppc64le.qcow2",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 636539904
            },
            "atomic_raw": {
              "name": "Fedora-AtomicHost-28-20180515.1",
              "image_name": "Fedora-AtomicHost-28-20180515.1.ppc64le.raw.xz",
              "image_url": "/pub/alt/atomic/stable/Fedora-Atomic-28-20180515.1/AtomicHost/ppc64le/images/Fedora-AtomicHost-28-20180515.1.ppc64le.raw.xz",
              "release": "28",
              "compose_id": "Fedora-Atomic-28-20180515.1",
              "size": 411513572
            }
          }
        }
        INFO:push-two-week-atomic.py:Fetching images information from compose ID Fedora-Atomic-28-20180515.1 complete
        INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): apps.fedoraproject.org
        INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): apps.fedoraproject.org
        INFO:push-two-week-atomic.py:Found aarch64, ec501e5a6833e6117632c3a7fc90ef17530399b6411ad9ba2c5c85f22cabe8dd
        INFO:push-two-week-atomic.py:Found ppc64le, dfe24e5d495ec16fbe2d61e6b494def2b119301f6565b8b6ecd542d79b02df89
        INFO:push-two-week-atomic.py:Found x86_64, a29367c58417c28e2bd8306c1f438b934df79eba13706e078fe8564d9e0eb32b
        INFO:push-two-week-atomic.py:Verifying and finding version of a29367c58417c28e2bd8306c1f438b934df79eba13706e078fe8564d9e0eb32b
        INFO:push-two-week-atomic.py:Verifying and finding version of ec501e5a6833e6117632c3a7fc90ef17530399b6411ad9ba2c5c85f22cabe8dd
        INFO:push-two-week-atomic.py:Verifying and finding version of dfe24e5d495ec16fbe2d61e6b494def2b119301f6565b8b6ecd542d79b02df89
        INFO:push-two-week-atomic.py:OSTREE COMMIT DATA INFORMATION
        INFO:push-two-week-atomic.py:{
          "aarch64": {
            "commit": "ec501e5a6833e6117632c3a7fc90ef17530399b6411ad9ba2c5c85f22cabe8dd",
            "version": "28.20180515.1",
            "ref": "fedora/28/aarch64/atomic-host",
            "previous_commit": "12a95314084eaa2242bdfe24197774aac163433d2405bc2813b4d89180434630"
          },
          "x86_64": {
            "commit": "a29367c58417c28e2bd8306c1f438b934df79eba13706e078fe8564d9e0eb32b",
            "version": "28.20180515.1",
            "ref": "fedora/28/x86_64/atomic-host",
            "previous_commit": "94a9d06eef34aa6774c056356d3d2e024e57a0013b6f8048dbae392a84a137ca"
          },
          "ppc64le": {
            "commit": "dfe24e5d495ec16fbe2d61e6b494def2b119301f6565b8b6ecd542d79b02df89",
            "version": "28.20180515.1",
            "ref": "fedora/28/ppc64le/atomic-host",
            "previous_commit": "d29c4549226ca8a50846360cf2f7149fbe15b4ab9d1c91d0d2aff1858b3ab1f3"
          }
        }
	INFO:push-two-week-atomic.py:Releasing ostrees at version: 28.20180515.1
	...
	<snip>


Verification
============

In order to verify this change has taken place, you should see emails on the
various mailing lists that are defined in the list ``ATOMIC_EMAIL_RECIPIENTS``
in the ``push-two-week-atomic.py`` script. At the time of this writing, those
are:

::

    ATOMIC_EMAIL_RECIPIENTS = [
        "devel@lists.fedoraproject.org"
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
.. _fedfind: https://pagure.io/fedora-qa/fedfind
