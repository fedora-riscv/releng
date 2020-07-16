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


#. Convert the .p7b formatted certificate to .pxf format:


   ::
        $ openssl pkcs7 -print_certs -in certificate.p7b -out certificate.cer
        $ openssl pkcs12 -export -in certificate.cer -inkey authenticode.key -out authenticode.pfx -certfile CACert.cer;


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

#. Export CERTPATH to the location where the .pfx file is located and make sure
   its named as authenticode.pfx and export CERTPASS to the file that contains the
   password used in creating .pvk file.

#. Run the build.sh script:

   ::

        $ ./build.sh

Verification
============
The FedoraMediaWriter-win32-<release_number>.exe is located under dist/win/ 
directory.

OS X:
-----

Build:
------

#. install xcode 8.1 from apple store.
#. install qt for mac from:
       http://download.qt.io/official_releases/qt/5.7/5.7.0/qt-opensource-mac-x64-clang-5.7.0.dmg
#. Open a terminal and run the following commands
 
   ::
        $ git clone https://github.com/MartinBriza/MediaWriter
        $ cd MediaWriter
        $ mkdir build
        $ cd build
        $ $QT_PREFIX/$QT_VERSION/clang64/bin/qmake ..
        $ make
        $ cp build/helper/mac/helper.app/Contents/MacOS/helper build/app/Fedora\ Media\ Writer.app/Contents/MacOS/
        $ cd build/app
        $ $QT_PREFIX/$QT_VERSION/clang_64/bin/macdeployqt "Fedora Media Writer.app" \
                -executable="Fedora Media Writer.app/Contents/MacOS/helper" -qmldir="../../app"

Prepare certificates
--------------------

This only needs to happen once per build machine, and prepares the certificates
by requesting them from Apple.

#. Install Xcode from the Mac App store
#. Start Xcode
#. Press Command-, (or in the menu bar click Xcode -> Preferences)
#. Go to Accounts tab
#. Click the plus button and sign in
#. Select the new account
#. Select the correct team
#. Click View Details
#. Under "Signing Identities", find "Developer ID Application"
#. Click Create
#. Wait until the button disappears
#. Done

Sign and DMG
------------

#. Open a terminal 
#. cd to the root directory of the FMW project
#. Run the following bash script:

   ::
        #/bin/bash

        security -v unlock-keychain login.keychain

        # First sign all dynamic libraries (dylib's)
        cd "build/app/Fedora Media Writer.app"
        for dylib in $(find  . -name "*dylib")
        do
             codesign -s "Developer ID Application: Fedora Gilmore" -v $dylib
        done
        # Now sign framework bundles
        for framework in $(find  . -name "*framework")
        do
             codesign -s "Developer ID Application: Fedora Gilmore" -v $framework
        done

        # Sign the two binaries
        codesign -s "Developer ID Application: Fedora Gilmore" -v Contents/MacOS/helper
        codesign -s "Developer ID Application: Fedora Gilmore" -v "Contents/MacOS/Fedora Media Writer"

        # Sign the app bundle
        codesign -s "Developer ID Application: Fedora Gilmore" -v .

        # Create the dmg
        cd ..
        rm -f FedoraMediaWriter-osx-*.dmg

        hdiutil create -srcfolder "Fedora Media Writer.app"  -format UDCO -imagekey zlib-level=9 -scrub \
                       -volname FedoraMediaWriter-osx FedoraMediaWriter-osx-$(git  describe --tags).dmg

Account Email(OS X)
-------------------

   ::
        releng@fedoraproject.org

Account Holders(OS X)
---------------------

#. Primary: Dennis Gilmore(ausil)
#. Backup: Kevin Fenzi(kevin)
#. Manager/bill-payer: Paul Frields(pfrields)

Consider Before Running
=======================
Nothing yet.

Issue with signing
=======================
If the build is done but it is not signed then try editing the ``build.sh``
and add -askpass argument for all the osslsigncode commands and run the script,
when it asks for the password you can enter the password that was used in
creating .pvk file.
