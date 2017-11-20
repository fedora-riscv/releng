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

* The Fedora Release number that you are going to release, example: ``-r 26``
* The Fedora key to sign the checksum metadata files with, example: ``-k
  fedora-26``

At the time of this writing, the `AutoCloud`_ tests are no longer reliable and
are effectively abandoned by those responsible. As such, on Atomic Host Two-Week
Release Day a member of the `Fedora Atomic WG`_ (normally ``dustymabe``) will
open a request to RelEng with the release candidate that should be released.

The request should contain a few key pieces of information. The pungi compose
id of the compose that created the media artifacts and optionally the pungi
compose id of the compose that created the ostrees (only if the media
and the ostree were created in different composes).

::

    pungi-compose-id: Fedora-Atomic-27-20171110.1
    ostree-pungi-compose-id: Fedora-27-20171110.n.1

Or the request may just contain the full command to run

::

    push-two-week-atomic.py -k fedora-27 -r 27 --pungi-compose-id Fedora-Atomic-27-20171110.1 --ostree-pungi-compose-id Fedora-27-20171110.n.1


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

    # Here we specify the signing key 'fedora-27' and are targeting the Fedora
    # Release '27' and specific pungi composes
	bodhi-backend01$ python push-two-week-atomic.py -k fedora-27 -r 27 --pungi-compose-id Fedora-Atomic-27-20171110.1 --ostree-pungi-compose-id Fedora-27-20171110.n.1
	INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): pagure.io
	INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): pagure.io
	INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): pagure.io
	INFO:push-two-week-atomic.py:Checking to make sure release is not currently blocked
	INFO:push-two-week-atomic.py:Querying datagrepper for latest AutoCloud successful tests
	INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): apps.fedoraproject.org
	INFO:push-two-week-atomic.py:TESTED_AUTOCLOUD_INFO
	{
	  "atomic_qcow2": {
		"release": "27",
		"image_url": "/pub/alt/atomic/stable/Fedora-Atomic-27-20171110.1/CloudImages/x86_64/images/Fedora-Atomic-27-20171110.1.x86_64.qcow2",
		"name": "Fedora-Atomic-27-20171110.1.",
		"compose_id": "Fedora-Atomic-27-20171110.1",
		"image_name": "Fedora-Atomic-27-20171110.1.x86_64.qcow2"
	  },
	  "atomic_vagrant_libvirt": {
		"release": "27",
		"image_url": "/pub/alt/atomic/stable/Fedora-Atomic-27-20171110.1/CloudImages/x86_64/images/Fedora-Atomic-Vagrant-27-20171110.1.x86_64.vagrant-libvirt.box",
		"name": "Fedora-Atomic-Vagrant-27-20171110.1.",
		"compose_id": "Fedora-Atomic-27-20171110.1",
		"image_name": "Fedora-Atomic-Vagrant-27-20171110.1.x86_64.vagrant-libvirt.box"
	  },
	  "atomic_raw": {
		"release": "27",
		"image_url": "/pub/alt/atomic/stable/Fedora-Atomic-27-20171110.1/CloudImages/x86_64/images/Fedora-Atomic-27-20171110.1.x86_64.raw.xz",
		"name": "Fedora-Atomic-27-20171110.1.",
		"compose_id": "Fedora-Atomic-27-20171110.1",
		"image_name": "Fedora-Atomic-27-20171110.1.x86_64.raw.xz"
	  },
	  "atomic_vagrant_virtualbox": {
		"release": "27",
		"image_url": "/pub/alt/atomic/stable/Fedora-Atomic-27-20171110.1/CloudImages/x86_64/images/Fedora-Atomic-Vagrant-27-20171110.1.x86_64.vagrant-virtualbox.box",
		"name": "Fedora-Atomic-Vagrant-27-20171110.1.",
		"compose_id": "Fedora-Atomic-27-20171110.1",
		"image_name": "Fedora-Atomic-Vagrant-27-20171110.1.x86_64.vagrant-virtualbox.box"
	  }
	}
	INFO:push-two-week-atomic.py:Query to datagrepper complete
	INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): apps.fedoraproject.org
	INFO:requests.packages.urllib3.connectionpool:Starting new HTTPS connection (1): apps.fedoraproject.org
	INFO:push-two-week-atomic.py:Found aarch64, da1bd08012699a0aacaa11481d3ed617477858aab0f2ea7300168ce106202255
	INFO:push-two-week-atomic.py:Found ppc64le, 362888edfac04f8848072ae4fb8193b3da2f4fd226bef450326faff4be290abd
	INFO:push-two-week-atomic.py:Found x86_64, d428d3ad8ecf44e53d138042bad56a10308883a0c5d64b9c51eff27fdc9da82c
	INFO:push-two-week-atomic.py:Verifying and finding version of d428d3ad8ecf44e53d138042bad56a10308883a0c5d64b9c51eff27fdc9da82c
	INFO:push-two-week-atomic.py:Verifying and finding version of da1bd08012699a0aacaa11481d3ed617477858aab0f2ea7300168ce106202255
	INFO:push-two-week-atomic.py:Verifying and finding version of 362888edfac04f8848072ae4fb8193b3da2f4fd226bef450326faff4be290abd
	INFO:push-two-week-atomic.py:OSTREE COMMIT DATA INFORMATION
	INFO:push-two-week-atomic.py:{
	  "aarch64": {
		"commit": "da1bd08012699a0aacaa11481d3ed617477858aab0f2ea7300168ce106202255",
		"version": "27.1",
		"ref": "fedora/27/aarch64/atomic-host",
		"previous_commit": "da1bd08012699a0aacaa11481d3ed617477858aab0f2ea7300168ce106202255"
	  },
	  "x86_64": {
		"commit": "d428d3ad8ecf44e53d138042bad56a10308883a0c5d64b9c51eff27fdc9da82c",
		"version": "27.1",
		"ref": "fedora/27/x86_64/atomic-host",
		"previous_commit": "d428d3ad8ecf44e53d138042bad56a10308883a0c5d64b9c51eff27fdc9da82c"
	  },
	  "ppc64le": {
		"commit": "362888edfac04f8848072ae4fb8193b3da2f4fd226bef450326faff4be290abd",
		"version": "27.1",
		"ref": "fedora/27/ppc64le/atomic-host",
		"previous_commit": "362888edfac04f8848072ae4fb8193b3da2f4fd226bef450326faff4be290abd"
	  }
	}
	INFO:push-two-week-atomic.py:Releasing ostrees at version: 27.1
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
