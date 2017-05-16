.. SPDX-License-Identifier:    CC-BY-SA-3.0


==========================
Finding Module Information
==========================

Description
===========
When users submit builds to the Module Build Service (MBS), it in turn submits
builds to Koji.  Sometimes, you are looking at a koji build, and you want to
know what module-build it is a part of.

Caveat
======

It requires that the build has been completed and has been tagged, until
https://pagure.io/fm-orchestrator/issue/375 is complete.

Setup
=====

Run the following::

    $ sudo dnf install python-arrow python-requests koji

Action
======

Run the following::

    $ scripts/mbs/koji-module-info.py $BUILD_ID
