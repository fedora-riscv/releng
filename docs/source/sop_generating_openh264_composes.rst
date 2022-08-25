.. SPDX-License-Identifier:    CC-BY-SA-3.0


============================
Generating Openh264 Composes
============================

Description
===========

Openh264 repos are a special case and we need to generate the composes for it in a different way.
We use ODCS to generate the private compose and send the rpms to Cisco to publish them on their CDN.
We publish the repodata on our side.

.. warning:: We do not have all the appropriate legal rights to distribute these packages, so we need to be extra carefull to make sure they are never distributed via our build system or websites

Action
======

Permissions needed
------------------

You will need some ODCS permissions in order to request private composes and composes from tags.
You can set this in infra/ansible in inventory/group_vars/odcs in the odcs_allowed_clients_users variable. See other releng users entries for format.

Get the odcs token
------------------

In order to generate an odcs compose, you need a openidc token.

Run the odcs-token.py under ``scripts/odcs/`` from pagure releng repository to generate the token.

::

    $ ./odcs-token.py

Make sure rpms are written out with the right signature
-------------------------------------------------------

::

    $ koji write-signed-rpm eb10b464 openh264-2.2.0-1.fc38

Where the key for that branch is listed, then the open264 package and version.

Generate a private odcs compose
-------------------------------

With the token generated above, generate the odcs private compose

::

    $ python odcs-private-compose.py <token> <koji_tag> <signingkeyid>

`koji_tag`: fxx-openh264 (Openh264 builds are tagged to fxx-openh264 tags where `xx` represents the fedora release)

`signingkeyid`: The short hash of the key for this Fedora branch. 

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
    # copy the src.rpm
    $ cp -rv 32-openh264/compose/Temporary/*/*/*/*/*src.rpm 32-rpms/
    $ cd 32-rpms
    # Create the tar file with the rpms
    $ tar -cJvf ../fedora-32-openh264-rpms.tar.xz *rpm

We need to send this tar file to Cisco along with the list of rpms in each tarball.

Syncing the compose to sundries01
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once we get a confirmation from Cisco that the rpms are updated on their CDN, verify them by using curl. For example:

::

    $ curl -I http://ciscobinary.openh264.org/openh264-2.1.1-1.fc32.x86_64.rpm

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

Extra info
^^^^^^^^^^

Normally that should be it, but in some cases you may want to push things out faster than normal, 
and here's a few things you can do to do that: 

On mm-backend01.iad2.fedoraproject.org you can run:

::

    # sudo -u mirrormanager /usr/local/bin/umdl-required codecs /var/log/mirrormanager/umdl-required.log

This will have mirrormanager scan the codecs dir and update it if it's changed. 

On batcave01.iad2.fedoraproject.org you can use ansible to force all the proxies to sync the codec content from sundries01:

::

    # nsible -a '/usr/bin/rsync --delete -a --no-owner --no-group sundries01::codecs.fedoraproject.org/ /srv/web/codecs.fedoraproject.org/' proxies

Mirrorlist servers should update every 15min.
