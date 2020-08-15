.. SPDX-License-Identifier:    CC-BY-SA-3.0


============================
Generating Openh264 Composes
============================

Description
===========

Openh264 repos are a special case and we need to generate the composes for it in a different way.
We use ODCS to generate the private compose and send the repos to Cisco to publish them on their CDN.

.. warning:: We do not have all the appropriate legal rights to distribute these packages, so we need to be extra carefull to make sure they are never distributed via our build system or websites

Action
======

Get the odcs token
------------------

In order to generate an odcs compose, you need a openidc token.

Run the odcs-token.py under ``scripts/odcs/`` from pagure releng repository to generate the token.

::

    $ python odcs-token.py

Generate a private odcs compose
-------------------------------

With the token generated in the privious step, generate the odcs private compose

::

    $ python odcs-private-compose.py <token> <koji_tag>

`koji_tag`: fxx-openh264 (Openh264 builds are tagged to fxx-openh264 tags where `xx` represents the fedora release)

The composes are stored under ``/srv/odcs/private/`` dir on ``odcs-backend-releng01.iad2.fedoraproject.org``

Pull the compose to your local machine
--------------------------------------

We need to extract the rpms and tar them to send them to Cisco.
In order to that, first of all we need to pull the compose to our local machine.

Move the compose to your home dir on odcs-backend-releng01.iad2.fedoraproject.org
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since the compose is owned by `odcs-server` pull it into your home dir

::

    $ mkdir ~/32-openh264
    $ sudo rsync -avhHP /srv/odcs/private/odcs-3835/ ~/32-openh264/
    $ sudo chown -R mohanboddu:mohanboddu ~/32-openh264/

Sync the compose to your local machine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pull in the compose from your home dir on odcs releng backend to your local machine into a temp working dir

::

    $ mkdir openh264-20200813
    $ scp -rv odcs-backend-releng01.iad2.fedoraproject.org:/home/fedora/mohanboddu/32-openh264/ openh264-20200813/

Make the changes needed
^^^^^^^^^^^^^^^^^^^^^^^

Please follow the following commands to make the necessary tar files to send to Cisco

::

    $ cd openh264-20200813
    $ mkdir 32-rpms
    # Copy rpms including devel rpms
    $ cp -rv 32-openh264/compose/Temporary/*/*/*/*/*rpm  32-rpms/
    # Copy debuginfo rpms
    $ cp -rv 32-openh264/compose/Temporary/*/*/*/*/*/*rpm 32-rpms/
    # Remove src.rpm
    $ rm 32-rpms/*src.rpm
    $ cd 32-rpms
    # Create the tar file with the rpms
    $ tar -cJvf ../fedora-32-openh264-rpms.tar.xz *rpm

We need to send this tar file to Cisco along with the list of rpms in each tarball.

Signing of repodata
^^^^^^^^^^^^^^^^^^^

Sync the compose from your local machine to bodhi-backend01.iad2.fedoraproject.org. As sigul is available there, you can sign the repodata on that box.

Create a working dir in the home dir on bodhi-backend01

::

    $ ssh bodhi-backend01.iad2.fedoraproject.org
    $ mkdir openh264-20200813

Now from you local machine scp the compose dir to bodhi-backend01

::

    $ scp -rv 32-openh264/ bodhi-backend01.iad2.fedoraproject.org:/home/fedora/mohanboddu/openh264-20200813

Go back to bodhi-backend01 and run the following commands

::

    $ ssh bodhi-backend01.iad2.fedoraproject.org
    # Sign the repodata
    $ for repodata in $(find ~/openh264-20200813/32-openh264/ -name repomd.xml); do sigul sign-data fedora-32 $repodata -o $repodata.asc; done
    # Change the perms of the the signed repodata
    $ find ~/openh264-20200813/32-openh264/ -name repomd.xml.asc | xargs chmod 664

Syncing the compose to sundries01
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once we get a confirmation from Cisco that the rpms are updated on their CDN, verify them by using curl. For example:

::

    $ curl -I http://ciscobinary.openh264.org/openh264-2.1.1-1.fc32.x86_64.rpm

Then pull the signed repodata compose to your local machine

::

    $ cd openh264-20200813/32-openh264
    $ rsync -avhHP bodhi-backend01.iad2.fedoraproject.org:/home/fedora/mohanboddu/openh264-20200825/32-openh264/ .

Now push these composes to **sundries01.iad2.fedoraproject.org** and **mm-backend01.iad2.fedoraproject.org**

On sundries01 we need to sync to a directory that is owned by *apache*, so first we sync to the home directory on sundries01. Same with mm-backend01 as the directory is owned by *root*.

Create a temp working directory on sundries01

::

    $ ssh sundries01.iad2.fedoraproject.org
    $ mkdir openh264-20200825

Create a temp working directory on mm-backend01

::

    $ ssh mm-backend01.iad2.fedoraproject.org
    $ mkdir openh264-20200825

Then from your local machine, sync the compose

::

    $ cd openh264-20200825
    $ rsync -avhHP 32-openh264 sundries01.iad2.fedoraproject.org:/home/fedora/mohanboddu/openh264-20200825
    $ rsync -avhHP 32-openh264 mm-backend01.iad2.fedoraproject.org:/home/fedora/mohanboddu/openh264-20200825

On sundries01

::

    $ cd openh264-20200825
    $ sudo rsync -avhHP 32-openh264/compose/Temporary/ /srv/web/codecs.fedoraproject.org/openh264/32/

On mm-backend01

::

    $ cd openh264-20200825
    $ sudo rsync -avhHP 32-openh264/compose/Temporary/ /srv/codecs.fedoraproject.org/openh264/32/
