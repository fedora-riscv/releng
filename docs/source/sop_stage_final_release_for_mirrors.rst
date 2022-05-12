.. SPDX-License-Identifier:    CC-BY-SA-3.0


===============================
Stage Final Release for Mirrors
===============================


Description
===========
When the release has been fully tested and approved at the "Go/No-Go" meeting
it is ready for release to the Fedora mirrors.

Action
======
#. Gather the needed info for running the staging script:
   Release Version: the numerical version number of the release ``24``
   ComposeID: The ID of the Compose
   Label: Compsoe label for the location in stage ``24_RC-1.2`` for example
   Key: the name of teh release key ``fedora-24`` or ``fedora-24-secondary`` as examples
   Prerelease: 0 or 1 sets if the release goes in test/ or not
   Arch: <optional> For secondary arches, changes some internal locations

   ::

        $ scripts/stage-release.sh 24 Fedora-24-20160614.0 24_RC-1.2 fedora-24 0


#. Sync the release to the Red Hat internal archive following internally documented

Check and set EOL on previous releases to reflect reality
=========================================================

#. check PDC for active releases and respective EOL date

#. if needed run the adjust-eol-all.py script from releng repository to correct any mistakes


Verification
============
Verification is somewhat difficult as one cannot look at the content via the
web server due to permissions.  Typically we ask somebody from the
Infrastructure team to give the tree a second set of eyes.

Consider Before Running
=======================
Hope the release is good!

