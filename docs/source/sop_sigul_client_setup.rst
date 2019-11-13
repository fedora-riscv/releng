.. SPDX-License-Identifier:    CC-BY-SA-3.0


==================
Sigul Client Setup
==================

This document describes how to configure a sigul client. For more information
on sigul, please see `User:Mitr <User-Mitr>`_

Prerequisites
=============


#. Install ``sigul`` and its dependencies. It is available in both Fedora and EPEL:

   On Fedora:

   ::

        dnf install sigul

   On RHEL/CentOS (Using EPEL):

   ::

        yum install sigul

#. Ensure that your koji certificate and the
   `Fedora CA certificates <Fedora-Cert>`_ are present on the system you're
   running the sigul client from at the following locations:

   * ``~/.fedora.cert``
   * ``~/.fedora-server-ca.cert``
   * ``~/.fedora-upload-ca.cert``

#. Admin privileges on koji are required to write signatures.

Configuration
=============

#. Run ``sigul_setup_client``
#. Choose a password for your NSS database. By default this will be stored on-disk in ``~/.sigul/client.conf``.
#. Choose an export password. You will only need to remember it until finishing
   ``sigul_setup_client``.
#. Enter the DB password you chose earlier, then the export password. You
   should see the message ``pk12util: PKCS12 IMPORT SUCCESSFUL``
#. Enter the DB password again. You should see the message ``Done``.
#. Assuming that you are running the sigul client within phx2, edit
   ``~/.sigul/client.conf`` to include the following lines: 

::

    [client]
    bridge-hostname: sign-bridge.phx2.fedoraproject.org
    server-hostname: sign-vault.phx2.fedoraproject.org

Updating your Fedora certificate
================================

When your Fedora certificate expires, after updating it run the following
commands:

::

    $ certutil -d ~/.sigul -D -n sigul-client-cert
    $ sigul_setup_client

.. _User-Mitr: https://fedoraproject.org/wiki/User:Mitr
.. _Fedora-Cert: https://fedoraproject.org/wiki/Package_maintenance_guide#Installing_fedpkg_and_doing_initial_setup
