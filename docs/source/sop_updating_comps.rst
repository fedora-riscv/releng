.. SPDX-License-Identifier:    CC-BY-SA-3.0


==============
Updating Comps
==============

Description
===========
When we start a new Fedora development cycle (when we branch rawhide) we have
to create a new comps file for the new release.  This SOP covers that action.

Action
======

#. clone the comps repo

   ::

        $ git clone ssh://git@pagure.io/fedora-comps.git

#. Create the new comps file for next release:

   ::

        $ cp comps-f24.xml.in comps-f25.xml.in

#. Edit Makefile to update comps-rawhide target

   ::

        - -comps-rawhide: comps-f24.xml
        - -       @mv comps-f24.xml comps-rawhide.xml
        +comps-rawhide: comps-f25.xml
        +       @mv comps-f25.xml comps-rawhide.xml

#. Add the new comps file to source control:

   ::

        $ git add comps-f25.xml.in

#. Edit the list of translated comps files in po/POTFILES.in to reflect
   currently supported releases.

   ::

        -comps-f22.xml
        +comps-f25.xml

#. Send it up:

   ::
        $ git push

Verification
============
One can review the logs for rawhide compose after this change to make sure
the right comps file was used.

Consider Before Running
=======================
Nothing yet.
