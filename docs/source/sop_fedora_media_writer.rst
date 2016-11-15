.. SPDX-License-Identifier:    CC-BY-SA-3.0


==============
Fedora Media Writer Building and Signing
==============

Description
===========
Whenever a new version of Fedora Media Writer is available, it is required
to build and code sign it.

Action
======

Windows
-------

#. Get a windows code signing key from any certification authority that is
   trusted by windows.

#. Convert the .pem formatted certificate to .pvk format:

   ::

        $ openssl rsa -in key.pem -outform PVK -pvk-strong -out authenticode.pvk

#. Convert the key file to .spc format:

   ::

        $ openssl crl2pkcs7 -nocrl -certfile cert.pem -outform DER -out authenticode.spc

#. Clone the Fedora Media Writer git repo:

   ::

        $ git clone https://github.com/MartinBriza/MediaWriter.git

#. Checkout the release tag for which the executable to be created:

   ::

        $ git checkout tags/<release_number>

#. The script to build and sign the executable is available at dist/win/build.sh
 
#. Get the mingw-mediawriter from koji. Make sure the version is the one that
   needs building and signing.

#. Install the remaining packages that are listed under PACKAGES variable in
   build.sh script.

#. Export CERTPATH to the location where the .pvk and .spc files are located and
   export CERTPASS to the password used in creating .pvk file.

#. Run the build.sh script:

   ::

        $ ./build.sh

Verification
============
The FedoraMediaWriter-win32-<release_number>.exe is located under dist/win/ 
directory.

Consider Before Running
=======================
Nothing yet.
