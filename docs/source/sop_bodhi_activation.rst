.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
Bodhi Activation Point
===========================

Description
===========
.. Put a description of the task here.

Bodhi must be activated after two weeks of `Mass Branching`_ at 00:00 UTC.

Action
======
.. Describe the action and provide examples

Run the following commands in the bodhi backend.

::
    $ bodhi-manage-releases create \
        --name F25 \
        --long-name "Fedora 25" \
        --id-prefix FEDORA \
        --version 25 \
        --branch f25 \
        --dist-tag f25 \
        --stable-tag f25-updates \
        --testing-tag f25-updates-testing \
        --candidate-tag f25-updates-candidate \
        --pending-stable-tag f25-updates-pending \
        --pending-testing-tag f25-updates-testing-pending \
        --override-tag f25-override \
        --state pending \
        --username <user_name>

Now the Koji tags should be edited so that Bodhi can push updates.

::
    $ koji edit-target f25-candidate --dest-tag f25-updates-candidate
    $ koji edit-target f25 --dest-tag f25-updates-candidate
    $ koji edit-tag --perm=admin f25

Email **devel-announce** and **test-announce** lists about Bodhi Activation. 
Please find the body of the email below:

::
  Hi all, 

  Today's an important day on the Fedora 25 schedule[1], with several significant cut-offs. First of all today is the Bodhi activation point [2]. That means that from now all Fedora 25 packages must be submitted to updates-testing and pass the relevant requirements[3] before they will be marked as 'stable' and moved to the fedora repository. 

  Today is also the Alpha freeze[4]. This means that only packages which fix accepted blocker or freeze exception bugs[5][6] will be marked as 'stable' and included in the Alpha composes. Other builds will remain in updates-testing until the Alpha release is approved, at which point the Alpha freeze is lifted and packages can move to 'stable' as usual until the Beta freeze.

  Today is also the Software String freeze[7], which means that strings marked for translation in Fedora-translated projects should not now be changed for Fedora 25. 

  Finally, today is the 'completion deadline' Change Checkpoint[8], meaning that Fedora 25 Changes must now be 'feature complete or close enough to completion that a majority of its functionality can be tested'. 

  Regards 
  <your_name>

  [1] https://fedoraproject.org/wiki/Releases/25/Schedule 
  [2] https://fedoraproject.org/wiki/Updates_Policy#Bodhi_enabling 
  [3] https://fedoraproject.org/wiki/Updates_Policy#Branched_release 
  [4] https://fedoraproject.org/wiki/Milestone_freezes 
  [5] https://fedoraproject.org/wiki/QA:SOP_blocker_bug_process 
  [6] https://fedoraproject.org/wiki/QA:SOP_freeze_exception_bug_process 
  [7] https://fedoraproject.org/wiki/ReleaseEngineering/StringFreezePolicy 
  [8] https://fedoraproject.org/wiki/Changes/Policy

Verification
============
.. Provide a method to verify that the action completed as expected (success)

The following message is displayed after successful completions of the bodhi command.

::
  Name:                F25
  Long Name:           Fedora 25
  Version:             25
  Branch:              f25
  ID Prefix:           FEDORA
  Dist Tag:            f25
  Stable Tag:          f25-updates
  Testing Tag:         f25-updates-testing
  Candidate Tag:       f25-updates-candidate
  Pending Testing Tag: f25-updates-testing-pending
  Pending Stable Tag:  f25-updates-pending
  Override Tag:        f25-override
  State:               pending

Consider Before Running
=======================
.. Create a list of things to keep in mind when performing action.

No considerations at this time. The docs git repository is simply a static
html hosting space and we can just re-render the docs and push to it again if
necessary.

.. _Mass Branching: https://docs.pagure.org/releng/sop_mass_branching.html 

