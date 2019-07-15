.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
Enabling Rawhide in Bodhi
===========================

Description
===========

This SOP covers the steps needed to enable Rawhide in Bodhi.


Create the release in Bodhi
---------------------------

In oder to start creating updates in Bodhi for rawhide, the release needs to be created
in Bodhi. Rawhide in Bodhi is represented by the Fedora version (ie Fedora 31), but it is set
in the prerelease state.


Add the koji tags
+++++++++++++++++

::

    $ koji add-tag --parent f31 f31-updates-candidate
    $ koji add-tag --parent f31 f31-updates-testing
    $ koji add-tag --parent f31-updates-testing f31-updates-testing-pending
    $ koji edit-tag --perm autosign f31-updates-testing-pending
    $ koji add-tag --parent f31 f31-updates-pending
    $ koji add-tag --parent f31 f31-override


Change the koji targets
+++++++++++++++++++++++

::

    $ koji edit-target f31 --dest-tag f31-updates-candidate
    $ koji edit-target f31-candidate --dest-tag f31-updates-candidate
    $ koji edit-target rawhide --dest-tag f31-updates-candidate

Create the release in bodhi
+++++++++++++++++++++++++++

::

    $ bodhi releases create --name "F31" --long-name "Fedora 31" --id-prefix FEDORA --version 31 --branch f31 \
      --dist-tag f31 --stable-tag f31 --testing-tag f31-updates-testing --candidate-tag f31-updates-candidate \
      --pending-stable-tag f31-updates-pending --pending-testing-tag f31-updates-testing-pending \
      --state pending --override-tag f31-override --create-automatic-updates --not-composed-by-bodhi


The important flags are `--not-composed-by-bodhi` which tells bodhi not to include the rawhide updates in the nightly pushes
and `--create-automatic-updates` which tells bodhi to automatically create an update listen to koji tag (build tagged with the pending-testing-tag) messages.


Bodhi configuration
+++++++++++++++++++

Bodhi is configured to required zero mandatory days in testing for the rawhide release.
This is done in ansible roles/bodhi2/base/templates/production.ini.j2 with the following.

::

    f{{ FedoraRawhideNumber }}.pre_beta.mandatory_days_in_testing = 0


Robosignatory configuration
+++++++++++++++++++++++++++

Robosignatory needs to be configured to signed the rawhide builds before these builds are tested by the CI pipeline.

::

    {
        "from": "f31-updates-candidate",
        "to": "f31-updates-testing-pending",
        "key": "fedora-31",
        "keyid": "3c3359c4"
    },


Branching Rawhide
-----------------

When it is time to branch rawhide, a new release should be created following the steps above, the existing release in bodhi should be modified has follow.

::
    $ bodhi releases edit --name "F31" --stable-tag f31-updates --no-create-automatic-updates --composed-by-bodhi

Robosignatory configuration
+++++++++++++++++++++++++++

Robosignatory configuration needs to be update to match the normal configuration of bodhi releases.

::

    {
        "from": "f31-signing-pending",
        "to": "f31-updates-testing-pending",
        "key": "fedora-31",
        "keyid": "3c3359c4"
    },
