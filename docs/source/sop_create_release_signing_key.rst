.. SPDX-License-Identifier:    CC-BY-SA-3.0


==========================
Create Release Signing Key
==========================

Description
===========
At the beginning of each release under development a new package signing key
is created for it.  This key is used to prove the authenticity of packages
built by Fedora and distributed by Fedora.  This key will be used to sign
all packages for the public test and final releases.

Action
======

Sigul
-----
Sigul is the signing server which holds our keys.  In order to make use of a
new key, the key will have to be created and access to the key will have to be
granted.  The ``new-key``, ``grant-key-access``, and ``change-passphrase``
commands are used.

::

    $ sigul new-key --help
    usage: client.py new-key [options] key

    Add a key

    options:
      -h, --help            show this help message and exit
      --key-admin=USER      Initial key administrator
      --name-real=NAME_REAL
                            Real name of key subject
      --name-comment=NAME_COMMENT
                            A comment about of key subject
      --name-email=NAME_EMAIL
                            E-mail of key subject
      --expire-date=YYYY-MM-DD
                            Key expiration date

    $ sigul grant-key-access --help
    usage: client.py grant-key-access key user

    Grant key access to a user

    options:
      -h, --help  show this help message and exit

    $ sigul change-passphrase --help
    usage: client.py change-passphrase key

    Change key passphrase

    options:
      -h, --help  show this help message and exit

For example if we wanted to create the Fedora 23 signing key, we would do the
following:

#. Log into a system configured to run sigul client.
#. Create the key using a strong passphrase when prompted

   ::

        $ sigul new-key --key-admin ausil --name-real Fedora \
                --name-comment 23 \
                --name-email fedora-23-primary@fedoraproject.org fedora-23

   For EPEL

   ::

        $ sigul new-key --key-admin ausil --name-real "Fedora EPEL" \
                --name-comment 7 \
                --name-email epel@fedoraproject.org epel-7

#. Wait a while for entropy.  This can take several minutes.
#. Grant key access to Fedora Account holders who will be signing packages and
   protect it with a temporary a passphrase.  For example, ``CHANGEME.``

   ::

        $ sigul grant-key-access fedora-23 kevin

.. note::
    **IMPORTANT:** Grant the access to autopen user as its required for robosignatory autosigning and then restart robosignatory service

#. Provide the key name and temporary passphrase to signers. If they don't
   respond, revoke access until they are ready to change their passphrase.
   Signers can change their passphrase using the ``change-passphrase`` command:

   ::

        $ sigul change-passphrase fedora-23

#. When your sigul cert expires, you will need to run:

   ::

        certutil -d ~/.sigul -D -n sigul-client-cert

   to remove the old cert, then

   ::

        sigul_setup_client

   to add a new one.

fedora-repos
------------
The fedora-repos package houses a copy of the public key information.  This
is used by rpm to verify the signature on files encountered.  Currently the
fedora-repos package has a single key file named after the version of the
key and the arch the key is for.  To continue our example, the file would be
named ``RPM-GPG-KEY-fedora-27-primary`` which is the primary arch key for
Fedora 27.  To create this file, use the ``get-public-key`` command from sigul:

::

    $ sigul get-public-key fedora-27 > RPM-GPG-KEY-fedora-27-primary

Add this file to the repo and update the archmap file for the new release.

::

    $ git add RPM-GPG-KEY-fedora-27-primary

Then make a new fedora-repos build for rawhide (``FIXME: this should be its own SOP``)

getfedora.org
-------------
getfedora.org/keys lists information about all of our keys.  We need to
let the websites team know we have created a new key so that they can add it to the
list.

We do this by filing an issues in their pagure instance
https://pagure.io/fedora-websites/
we should point them at this SOP

Web team SOP
^^^^^^^^^^^^

::

    # from git repo root
    cd fedoraproject.org/
    curl $KEYURL > /tmp/newkey
    $EDITOR update-gpg-keys # Add key ID of recently EOL'd version to obsolete_keys
    ./update-gpg-key /tmp/newkey
    gpg static/fedora.gpg # used to verify the new keyring
    # it should look something like this:
    # pub  4096R/57BBCCBA 2009-07-29 Fedora (12) <fedora@fedoraproject.org>
    # pub  4096R/E8E40FDE 2010-01-19 Fedora (13) <fedora@fedoraproject.org>
    # pub  4096R/97A1071F 2010-07-23 Fedora (14) <fedora@fedoraproject.org>
    # pub  1024D/217521F6 2007-03-02 Fedora EPEL <epel@fedoraproject.org>
    # sub  2048g/B6610DAF 2007-03-02 [expires: 2017-02-27]
    # it must only have the two supported versions of fedora, rawhide and EPEL
    # also verify that static/$NEWKEY.txt exists
    $EDITOR data/content/{keys,verify}.html # see git diff 1840f96~ 1840f96

sigulsign_unsigned
------------------
``sigulsign_unsigned.py`` is the script Release Engineers use to sign content in
koji.  This script has a hardcoded list of keys and aliases to the keys that
needs to be updated when we create new keys.

Add the key details to the ``KEYS`` dictionary near the top of the
``sigulsign_unsigned.py`` script.  It lives in Release Engineering's git repo
at ``ssh://git@pagure.io/releng.git`` in the ``scripts`` directory. You
will need to know the key ID to insert the correct information:

::

    $ gpg <key block from sigul get-public-key>

Public Keyservers
-----------------
We upload the key to the public key servers when we create the keys.  To do
this, we need to get the ascii key block from sigul, determine the key ID,
import they key into our local keyring, and then upload it to the key servers.

::

    $ sigul get-public-key fedora-13 > fedora-13
    $ gpg fedora-13 (The ID is the "E8E40FDE" part of 4096R/E8E40FDE)
    $ gpg --import fedora-13
    $ gpg --send-keys E8E40FDE

pungi-fedora
----
The nightly compose configs come from the pungi-fedora project on https://pagure.io
We need to create a pull request to pull in the new key.

::

    $ git clone ssh://git@pagure.io/<your fork path>/pungi-fedora.git
    $ cd pungi-fedora
    $ vim *conf
    <set key value in sigkeys = line >
    $ git commit -m 'Add new key'
    $ git push
    $ file a Pull Request


Koji
----
Koji has a garbage collection utility that will find builds that meet criteria
to be removed to save space.  Part of that criteria has to do with whether or
not the build has been signed with a key.  If the collection utility doesn't
know about a key it will ignore the build.  Thus as we create new keys we need
to inform the utility of these keys or else builds can pile up.  The
configuration for the garbage collection lives within ansible.

On a clone of the infrastructure ansible git repo edit the
roles/koji_hub/templates/koji-gc.conf.j2 file:

::

    diff --git a/roles/koji_hub/templates/koji-gc.conf.j2 b/roles/koji_hub/templates/koji-gc.conf.j2
    index 9ecb750..9c48a8e 100644
    --- a/roles/koji_hub/templates/koji-gc.conf.j2
    +++ b/roles/koji_hub/templates/koji-gc.conf.j2
    @@ -35,6 +35,7 @@ key_aliases =
         81B46521    fedora-24
         FDB19C98    fedora-25
         64DAB85D    fedora-26
    +    F5282EE4    fedora-27
         217521F6    fedora-epel
         0608B895    fedora-epel-6
         352C64E5    fedora-epel-7
    @@ -52,6 +53,7 @@ unprotected_keys =
         fedora-24
         fedora-25
         fedora-26
    +    fedora-27
         fedora-extras
         redhat-beta
         fedora-epel
    @@ -91,6 +93,7 @@ policy =
         sig fedora-24 && age < 12 weeks :: keep
         sig fedora-25 && age < 12 weeks :: keep
         sig fedora-26 && age < 12 weeks :: keep
    +    sig fedora-27 && age < 12 weeks :: keep
         sig fedora-epel && age < 12 weeks :: keep
         sig fedora-epel-6 && age < 12 weeks :: keep
         sig fedora-epel-7 && age < 12 weeks :: keep

In this case the fedora-epel key was added to the list of key aliases, then
referenced in the list of unprotected_keys, and finally a policy was created
for how long to keep builds signed with this key.

Once you've made your change commit and push.  The buildsystem will pick up
this change the next time puppet refreshes.

Verification
============
We can verify that the key was created in sigul, the correct users have access
to the key, the key was added to the fedora-release package, that the website
was updated with the right key, that sigulsign_unsigned was properly updated,
and that the key was successfully updated to the public key servers.

sigul
-----
Use the ``list-keys`` command to verify that the key was indeed added to sigul:

::

    $ sigul list-keys
    Administrator's password:
    fedora-10
    fedora-10-testing
    fedora-11
    fedora-12
    fedora-13

Our new key should be on the list.  This command expects **your**
administrative password.

Use the ``list-key-users`` command to verify all the signers have access:

::

        $ sigul list-key-users fedora-13
        Key passphrase:
        jkeating
        jwboyer

This command expects **your** key passphrase for the key in question.

fedora-release
--------------
To verify that the key was added to this package correctly, download the latest
build from koji and run rpm2cpio on it, then run gpg on the key file:

::

    $ koji download-build --arch noarch --latest f27 fedora-repos
    fedora-repos-rawhide-27-0.1.noarch.rpm                  | 7.3 kB  00:00:00
    fedora-repos-27-0.1.noarch.rpm                          |  87 kB  00:00:00
    $ rpmdev-extract fedora-repos-27-0.1.noarch.rpm
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-27-fedora
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-10-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-10-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-10-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-10-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-10-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-11-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-11-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-11-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-11-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-11-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-12-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-12-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-12-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-12-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-12-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-arm
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-mips
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-13-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-14-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-14-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-14-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-arm
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-15-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-arm
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-16-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-arm
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-17-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-arm
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-18-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-19-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-20-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-21-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-22-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-s390
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-23-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-24-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-25-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-26-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-aarch64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-armhfp
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-ppc64le
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-s390x
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-7-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-8-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-8-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-8-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-8-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-8-primary-original
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-8-x86_64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-i386
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-ia64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-ppc
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-ppc64
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-primary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-primary-original
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-secondary
    fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-9-x86_64
    fedora-repos-27-0.1.noarch/etc/yum.repos.d
    fedora-repos-27-0.1.noarch/etc/yum.repos.d/fedora-cisco-openh264.repo
    fedora-repos-27-0.1.noarch/etc/yum.repos.d/fedora-updates-testing.repo
    fedora-repos-27-0.1.noarch/etc/yum.repos.d/fedora-updates.repo
    fedora-repos-27-0.1.noarch/etc/yum.repos.d/fedora.repo

    $ gpg2 fedora-repos-27-0.1.noarch/etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-27-primary
    pub   rsa4096 2017-02-21 [SCE]
          860E19B0AFA800A1751881A6F55E7430F5282EE4
    uid           Fedora 27 (27) <fedora-27@fedoraproject.org>
        pub  4096R/E8E40FDE 2010-01-19 Fedora (13) <fedora@fedoraproject.org>

You may wish to do this in a tempoary directory to make cleaning it up easy.

getfedora.org
-----------------
One can simply browse to https://getfedora.org/keys to verify that the key
has been uploaded.

sigulsign_unsigned
------------------
The best way to test whether or not the key has been added correctly is to
sign a package using the key, like our newly built fedora-repos package.

::

    $ ./sigulsign_unsigned.py fedora-13 fedora-release-13-0.3
    Passphrase for fedora-13:

The command should exit cleanly.

Public key servers
------------------
One can use the <code>search-keys</code> command from gpg to locate the key on the public server:

::

    $ gpg2 --search-keys "Fedora (13)"
    gpg: searching for "Fedora (13)" from hkp server subkeys.pgp.net
    (1) Fedora (13) <fedora@fedoraproject.org>
          4096 bit RSA key E8E40FDE, created: 2010-01-19
    ...

Koji
----
Log into koji02.phx2.fedoraproject.org by way of bastion.fedoraproject.org.

Verify that ``/etc/koji-gc/koji-gc.conf`` has the new key in it.

Consider Before Running
=======================

Nothing at this time.

