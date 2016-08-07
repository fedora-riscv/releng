.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========
End Of Life
===========

Description
===========
Each release of Fedora is maintained as laid out in the `maintenance
schedule`_. At the conclusion of the maintenance period, a Fedora release
enters ``end of life`` status. This procedure describes the tasks necessary to
move a release to that status.

Actions
=======

Set date
--------
* Releng responsibilities:
    * Follow guidelines of `maintenance schedule`_
    * Take into account any infrastructure or other supporting project resource
      contention
    * Announce the closure of the release to the package maintainers.

Reminder announcement
---------------------
* from rel-eng to f-devel-announce, f-announce-l, including
    * date of last update push (if needed)
    * date of actual EOL

Koji tasks
----------
* disable builds by removing targets

  ::

    koji remove-target f19
    koji remove-target f19-updates-candidate

* Purge from disk the signed copies of rpms that are signed with the EOL'd
  release key

Bodhi tasks
-----------
* Run the following end of life script from bodhi backend
  ::
    bodhi-manage-releases edit --name F21 --state archived


PackageDB
---------

Set the release to be End of Life in the PackageDB. A admin can login and do
this from the web interface.

Source Control (git)
--------------------

* Branches for new packages in git are not allowed for distribution X after
  the Fedora X+2 release. New builds are no longer allowed for EOL Fedora
  releases.

Fedora Program Manager Tasks
----------------------------

* Close all open bugs
* `End of Life Process`_

Bugzilla
--------

* Update the description of Fedora in bugzilla for the current releases.
    * Get someone from sysadmin-main to login as the
      fedora-admin-xmlrpc@redhat.com user to bugzilla.
    * Have them edit the description of the Fedora product here:
      https://bugzilla.redhat.com/editproducts.cgi?action=edit&product=Fedora

Docs tasks
----------

* any?

Badges tasks
------------

* Update the `cold undead hands`_ badge.

    * In order to do this, you need to be in the `sysadmin-badges` group and the
      `gitbadges` group.  If you're not, just email those two groups at
      `sysadmin-badges-members@fedoraproject.org` and
      `gitbadges-members@fedoraproject.org`.  Tell them that they need to update
      this badge and point them to these instructions.
    * Clone the repo with `` $ git clone https://git.fedorahosted.org/git/badges.git``
    * Edit `rules/you-can-pry-it-from-my-cold-undead-hands.yml` and add the EOL
      release to the list in the trigger section on line 19.
    * Push that back to fedorahosted.
    * Push the rule change out live to our servers by logging into batcave and
      running the `manual/push-badges.yml` playbook.
      https://infrastructure.fedoraproject.org/cgit/ansible.git/tree/playbooks/manual/push-badges.yml
    * All done.

Cloud tasks
-----------

.. note::
    FIXME: This needs updating, I'm pretty sure we need to do something with
    fedimg here

* Remove unsupported EC2 images from
  https://fedoraproject.org/wiki/Cloud_images#Currently_supported_EC2_images

Taskotron tasks
---------------

`File Taskotron ticket`_ and ask for the EOL'd release support to be removed.
(Log in to Phabricator using your FAS_account@fedoraproject.org email address).

Final announcement
------------------

* from releng to f-announce-l
    * on EOL date if at all possible
    * link to previous reminder announcement (use HTTPS)

Announcement content
^^^^^^^^^^^^^^^^^^^^


* As of the <eol_date>, Fedora X has reached its end of life for
  updates and support. No further updates, including security updates,
  will be available for Fedora X. A previous reminder was sent on 
  <announcement_daet> [0]. Fedora X+1 will continue to receive updates until
  approximately one month after the release of Fedora X+3. The
  maintenance schedule of Fedora releases is documented on the Fedora
  Project wiki [1]. The Fedora Project wiki also contains instructions
  [2] on how to upgrade from a previous release of Fedora to a version
  receiving updates.

  <your_name>.

  [0]<url to the announcement from announce@lists.fedoraproject.org list>
  [1]https://fedoraproject.org/wiki/Fedora_Release_Life_Cycle#Maintenance_Schedule
  [2]https://getfedora.org/

.. note::
       All dates should follow xxth of month year format.(Example: 19th of July 2016)

Update eol wiki page
^^^^^^^^^^^^^^^^^^^^

https://fedoraproject.org/wiki/End_of_life update with release and number of
days.

Verification
============

.. note::
    FIXME: This section needs some love

Consider Before Running
=======================
* Resource contention in infrastructure, such as outages
* Extenuating circumstances for specific planned updates, if any
* ot

.. _maintenance schedule:
    https://fedoraproject.org/wiki/Fedora_Release_Life_Cycle#Maintenance_Schedule
.. _End of Life Process:
    https://fedoraproject.org/wiki/BugZappers/HouseKeeping#End_of_Life_.28EOL.29
.. _cold undead hands:
    https://git.fedorahosted.org/cgit/badges.git/tree/rules/you-can-pry-it-from-my-cold-undead-hands.yml
.. _File Taskotron ticket:
    https://phab.qadevel.cloud.fedoraproject.org/maniphest/task/edit/form/default/?title=release%20is%20EOL&priority=80&tags=libtaskotron
