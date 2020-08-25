.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
Bodhi Activation Point
===========================

Description
===========
.. Put a description of the task here.

Bodhi must be activated after two weeks of `Mass Branching`_ at 14:00 UTC.

Action
======
.. Describe the action and provide examples

Making koji changes
^^^^^^^^^^^^^^^^^^^

Make the following koji tag changes

::

  $ koji remove-tag-inheritance f33-updates-candidate f33
  $ koji remove-tag-inheritance f33-updates-testing f33
  $ koji remove-tag-inheritance f33-updates-pending f33
  $ koji remove-tag-inheritance f33-override f33
  $ koji add-tag-inheritance f33-updates-candidate f33-updates
  $ koji add-tag-inheritance f33-updates-testing f33-updates
  $ koji add-tag-inheritance f33-updates-pending f33-updates
  $ koji add-tag-inheritance f33-override f33-updates
  $ koji edit-tag --perm=admin f33

Update bodhi rpm release
^^^^^^^^^^^^^^^^^^^^^^^^

Set the bodhi rpm to release to not to automatically create the update and also bodhi knows to compose the updates

::

  $ bodhi releases edit --name "F33" --stable-tag f33-updates --testing-repository updates-testing --package-manager dnf --no-create-automatic-updates --composed-by-bodhi

Add the modular release
^^^^^^^^^^^^^^^^^^^^^^^

Run the following command on your own workstation to add the modular release

::

  $ bodhi releases create --name F33M --long-name "Fedora 33 Modular" --id-prefix FEDORA-MODULAR --version 33 --branch f33m --dist-tag f33-modular --stable-tag f33-modular-updates --testing-tag f33-modular-updates-testing --candidate-tag f33-modular-updates-candidate --pending-stable-tag f33-modular-updates-pending --pending-testing-tag f33-modular-updates-testing-pending --pending-signing-tag f33-modular-signing-pending --override-tag f33-modular-override --state pending --user mohanboddu

.. warning:: Due to a `bug <https://github.com/fedora-infra/bodhi/issues/2177>`_ in Bodhi, it is
    critical that Bodhi processes be restarted any time ``bodhi releases create`` or
    ``bodhi releases edit`` are used.

.. note:: Add the container and flatpak releases if they weren't already added to bodhi

Ansible Changes
===============

Update vars
^^^^^^^^^^^

Update the *FedoraBranchedBodhi* and *RelEngFrozen* vars in infra ansible

::

  diff --git a/vars/all/FedoraBranchedBodhi.yaml b/vars/all/FedoraBranchedBodhi.yaml
  index aba8be2..606eb2e 100644
  --- a/vars/all/FedoraBranchedBodhi.yaml
  +++ b/vars/all/FedoraBranchedBodhi.yaml
  @@ -3,4 +3,4 @@
  # prebeta: After bodhi enablement/beta freeze and before beta release
  # postbeta: After beta release and before final release
  # current: After final release
  -FedoraBranchedBodhi: preenable
  +FedoraBranchedBodhi: prebeta
  diff --git a/vars/all/RelEngFrozen.yaml b/vars/all/RelEngFrozen.yaml
  index 5836689..87d85f3 100644
  --- a/vars/all/RelEngFrozen.yaml
  +++ b/vars/all/RelEngFrozen.yaml
  @@ -1 +1 @@
  -RelEngFrozen: False
  +RelEngFrozen: True

Update Greenwave Policy
^^^^^^^^^^^^^^^^^^^^^^^

Now edit the Greenwave policy to configure a policy for the new release by editing
``roles/openshift-apps/greenwave/templates/configmap.yml`` in the Infrastructure Ansible repository.

:: 

  diff --git a/roles/openshift-apps/greenwave/templates/fedora.yaml b/roles/openshift-apps/greenwave/templates/fedora.yaml
  index 7a76f61..d15e154 100644
  --- a/roles/openshift-apps/greenwave/templates/fedora.yaml
  +++ b/roles/openshift-apps/greenwave/templates/fedora.yaml
  @@ -84,6 +84,9 @@ rules:
  --- !Policy
  id: "no_requirements_testing"
  product_versions:
  +  - fedora-33-modular
  +  - fedora-33-containers
  +  - fedora-33-flatpaks
    - fedora-32-modular
    - fedora-32-containers
    - fedora-32-flatpaks
  @@ -107,6 +110,9 @@ rules: []
  --- !Policy
  id: "no_requirements_for_stable"
  product_versions:
  +  - fedora-33-modular
  +  - fedora-33-containers
  +  - fedora-33-flatpaks
    - fedora-32-modular
    - fedora-32-containers
    - fedora-32-flatpaks
  @@ -133,6 +139,7 @@ id: "openqa_release_critical_tasks_for_testing"
  product_versions:
    - fedora-rawhide
    - fedora-eln
  +  - fedora-33
    - fedora-32
    - fedora-31
    - fedora-30
  @@ -147,6 +154,7 @@ id: "openqa_release_critical_tasks_for_stable"
  product_versions:
    - fedora-rawhide
    - fedora-eln
  +  - fedora-33
    - fedora-32
    - fedora-31
    - fedora-30

Update Robosignatory Config
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Update the robosignatory config in the infra ansible repo as following

::

  diff --git a/roles/robosignatory/templates/robosignatory.toml.j2 b/roles/robosignatory/templates/robosignatory.toml.j2
  index 16a6708..68f4251 100644
  --- a/roles/robosignatory/templates/robosignatory.toml.j2
  +++ b/roles/robosignatory/templates/robosignatory.toml.j2
  @@ -259,8 +259,8 @@ handlers = ["console"]
              type = "modular"
  
              [[consumer_config.koji_instances.primary.tags]]
  -            from = "f33-modular-updates-candidate"
  -            to = "f33-modular"
  +            from = "f33-modular-signing-pending"
  +            to = "f33-modular-updates-testing-pending"
              key = "{{ (env == 'production')|ternary('fedora-33', 'testkey') }}"
              keyid = "{{ (env == 'production')|ternary('9570ff31', 'd300e724') }}"
              type = "modular"

Run the playbooks
^^^^^^^^^^^^^^^^^

::

    $ rbac-playbook openshift-apps/greenwave.yml
    $ rbac-playbook openshift-apps/bodhi.yml
    $ rbac-playbook groups/bodhi-backend.yml
    $ rbac-playbook groups/releng-compose.yml
    $ rbac-playbook manual/autosign.yml

Greenwave runs in OpenShift (as implied by the playbook paths), and so the change will not be live
right away when the playbook finishes. You can monitor
https://greenwave-web-greenwave.app.os.fedoraproject.org/api/v1.0/policies to wait for the new
policy to appear (it should take a few minutes).

Restart bodhi services
^^^^^^^^^^^^^^^^^^^^^^

Restart bodhi services to understand the bodhi new release on bodhi-backend01
(Look at warning in https://docs.pagure.org/releng/sop_bodhi_activation.html#action and the bug is https://github.com/fedora-infra/bodhi/issues/2177)

::

  $ sudo systemctl restart bodhi-celery
  $ sudo systemctl restart fm-consumer@config
  $ sudo systemctl restart koji-sync-listener

Send Announcement
^^^^^^^^^^^^^^^^^

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

Compare koji tagging structure with older release

::

  $ koji list-tag-inheritance <branched_release> --reverse
  $ koji list-tag-inheritance <latest_stable_release> --reverse

Compare the bodhi release with older release

::

  $ bodhi releases info <branched_release>
  $ bodhi releases info <latest_stable_release>

Check for other variants like modular, container and flatpaks

Consider Before Running
=======================
.. Create a list of things to keep in mind when performing action.

No considerations at this time. The docs git repository is simply a static
html hosting space and we can just re-render the docs and push to it again if
necessary.

.. _Mass Branching: https://docs.pagure.org/releng/sop_mass_branching.html 

