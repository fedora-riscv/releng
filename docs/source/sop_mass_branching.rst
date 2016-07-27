.. SPDX-License-Identifier:    CC-BY-SA-3.0


==============
Mass Branching
==============

Description
===========

At each alpha freeze we branch the pending release away from ``devel/`` which
allows rawhide to move on while the pending release goes into bugfix and
polish mode.

Action
======

Dist-Git
--------

The default process when we create new branches is to have them point to the
first commit ever in the repo, this is fine for any new branches but the ones
creating during the mass-branching process.

So the script that generates these branches must be adjsuted during the
mass-branching to behave as desired and then put back to its default.

On pkgs01 (or pkgs01.stg), edit the file
``/usr/local/bin/pkgdb_sync_git_branches.py``

::

	 GIT_FOLDER = '/srv/git/repositories/'
 	
	-MKBRANCH = '/usr/local/bin/mkbranch'
	+#MKBRANCH = '/usr/local/bin/mkbranch'
	+MKBRANCH = '/usr/local/bin/mkbranch_branching'
	 SETUP_PACKAGE = '/usr/local/bin/setup_git_package'

This will make the script calls ``/usr/local/bin/mkbranch_branching`` when
creating the new branches.


PackageDB
---------

Mass branching in the pkgdb is the first step. It should be done near the time
that the scm branches are created so as not to confuse packagers.  However, it
does not cause an outage so it could be done ahead of time.

The action on pkgdb has been simplified to a single step:

#. On one of the pkgdb host (ie: pkgdb01 or pkgdb02 or pkgdb01.stg if you want 
   to try on staging first), call the script pkgdb2_branch.py:

   ::

        sudo pkgdb2_branch.py --user=<fas_user> --groups=<fas_group_allowed>  fXX

   ``fas_user`` corresponds to the FAS username of the admin doing the action.

   ``fas_group_allowed`` corresponds to a FAS group allowed to perform admin
   actions (ie: ADMIN_GROUP in the `pkgdb configuration file`_)

   ``fXX`` is the new Fedora version (for example f25)

The script will ask you for the new dist-tag for rawhide (.fcn+1) then ask you
to create the new Fedora collection (Fn) in the database then actually start the
branching process. This can take a little time dependending on the database size
as well as the load on the database server.

When the branching is finished, the email address defined at MAIL_ADMIN in the
configuration file will receive an email that tells which were branched and
which were unbranched.

If something fails spectacularly, it is safe to try mass branching again at a
later time, you may want to specify then ``--nocreate`` to skip the steps asking
to update rawhide and create the new collection in the database.  If only a few
cleanups a re needed it might be better to do that with the regular branch
commands.


Ansible
-------

A couple files in ansible need to be updated to be aware of a new branch.


genacls.pkgdb
^^^^^^^^^^^^^

The other file is ran by cron that will read data out of pkgdb and construct an
ACL config file for our scm.  It has a section that lists active branches to
deal with as pkgdb will provide data for all branches.

In a clone of the ansible repository, edit the file:
``roles/distgit/templates/genacls.pkgdb``

::

	diff --git a/roles/distgit/templates/genacls.pkgdb b/roles/distgit/templates/genacls.pkgdb
	index b4b52f2..c65f118 100644
	--- a/ roles/distgit/templates/genacls.pkgdb
	+++ b/ roles/distgit/templates/genacls.pkgdb
	@@ -38,6 +38,7 @@ if __name__ == '__main__':
	         'F-11': 'f11', 'F-12': 'f12', 'F-13': 'f13', 'f14': 'f14', 'f15':
	         'f15', 'f16': 'f16', 'f17': 'f17', 'f18': 'f18', 'f19': 'f19',
	         'f20': 'f20', 'f21': 'f21', 'f22': 'f22', 'f23': 'f23', 'f24': 'f24',
	+        'f25': 'f25',
	         'devel': 'master', 'master': 'master'}
	
	     # Create a "regex"ish list 0f the reserved branches


fedora-packages
^^^^^^^^^^^^^^^

There is a file in the fedora-packages webapp source that needs to be updated
with new releases.  It tells fedora-packages what tags to ask koji about. Just
like before, make the following edit the ansible repo:

::

    diff --git a/roles/packages3/web/files/distmappings.py b/roles/packages3/web/files/distmappings.py
    index c72fd4b..b1fbaa5 100644
    --- a/roles/packages3/web/files/distmappings.py
    +++ b/roles/packages3/web/files/distmappings.py
    @@ -1,5 +1,9 @@
     # Global list of koji tags we care about
    -tags = ({'name': 'Rawhide', 'tag': 'f20'},
    +tags = ({'name': 'Rawhide', 'tag': 'f21'},
    +
    +        {'name': 'Fedora 20', 'tag': 'f20-updates'},
    +        {'name': 'Fedora 20', 'tag': 'f20'},
    +        {'name': 'Fedora 20 Testing', 'tag': 'f20-updates-testing'},

             {'name': 'Fedora 19', 'tag': 'f19-updates'},
             {'name': 'Fedora 19', 'tag': 'f19'},
    @@ -13,10 +17,6 @@ tags = ({'name': 'Rawhide', 'tag': 'f20'},
             {'name': 'Fedora 17', 'tag': 'f17'},
             {'name': 'Fedora 17 Testing', 'tag': 'f17-updates-testing'},

    -        {'name': 'Fedora 16', 'tag': 'f16-updates'},
    -        {'name': 'Fedora 16', 'tag': 'f16'},
    -        {'name': 'Fedora 16 Testing', 'tag': 'f16-updates-testing'},
    -
             {'name': 'EPEL 6', 'tag': 'dist-6E-epel'},
             {'name': 'EPEL 6', 'tag': 'dist-6E-epel-testing'},

Push the changes
^^^^^^^^^^^^^^^^

When done editing the files, commit, push and apply them via the corresponding
ansible playbook:

::

	playbooks/groups/pkgs.yml -t distgit -t config
    playbooks/groups/packages.yml -t packages/web


SCM
---

The following work is performed on pkgs01


Update ACLs and create the branches
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Start manually the process to create the branches and update the ACLS:

::

    $ sudo -u jkeating /usr/local/bin/genacls.sh

Undo change to the new branch process
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As explained earlier, the process to create new branches in git repo differs
during the mass-branching compared to the rest of the time. So let's undo the
changes made to ``/usr/local/bin/pkgdb_sync_git_branches.py``

::

	 GIT_FOLDER = '/srv/git/repositories/'
 	 
	-#MKBRANCH = '/usr/local/bin/mkbranch'
	+MKBRANCH = '/usr/local/bin/mkbranch'
	-MKBRANCH = '/usr/local/bin/mkbranch_branching'
	 SETUP_PACKAGE = '/usr/local/bin/setup_git_package'
 	 
	 THREADS = 20


Taskotron
---------
`File a Taskotron ticket`_ and ask for the newly branched release support to
be added. (Log in to Phabricator using your FAS_account@fedoraproject.org
email address).


Koji
----
The koji build system needs to have some tag/target work done to handle builds
from the new branch and to update where builds from master go. See the
:ref:`section on Koji in the Adding Build Targets SOP <adding_build_targets_koji>`
for details.


Fedora Release
--------------
The Fedora release package needs to be updated in both the new branch and in
master.

.. note::
    FIXME Link to fedora release bump SOP ... FIXME Does that SOP exist?


Bodhi
-----
Bodhi needs to be turned on for the new branch. Instructions in the `Bodhi SOP`_


Enable nightly branched compose
-------------------------------
A cron job needs to be modified and turned on for the new branch.

.. note::
    FIXME Link to nightly branched SOP ... Does that SOP exist?


Update kickstart used by nightly live ISOs
------------------------------------------

On a nightly basis, a live ISO image is created for each `spin`_ and hosted at
http://alt.fedoraproject.org/pub/fedora/linux/development/rawhide/Spins/. The
`dnf`_/`yum`_ repositories used by  `spin-kickstarts`_ need to be updated to
use the branched repository.  Please `file a rel-eng ticket`_ to request updating
the kickstart file used to generate the nightly spin ISO's.


Comps
-----
A new comps file needs to be created for the next fedora release (the one after
what we just branched for).

Please see :doc:`sop_updating_comps`


Mock
----
Mock needs to be updated to have configs for the new branch.  This should
actually be done and pushed just before the branch event.

.. note::
    FIXME Link to mock update SOP ... does that exist?


MirrorManager
-------------
Mirror manager will have to be updated so that the `dnf`_/`yum`_ repo
redirections are going to the right places.

.. note::
    FIXME Link to MM SOP ... exists?


Update critpath
---------------

Packagedb has information about which packages are critpath and which are not.
A script that reads the `dnf`_/`yum`_ repodata (critpath group in comps, and
the package dependencies) is used to generate this.  Read
:doc:`sop_update_critpath` for the steps to take.


Consider Before Running
=======================

.. note::
    FIXME: Need some love here

.. _master collection: https://admin.fedoraproject.org/pkgdb/collection/master/
.. _Admin interface of pkgdb: https://admin.fedoraproject.org/pkgdb/admin/
.. _Final Freeze: https://fedoraproject.org/wiki/Schedule
.. _pkgdb configuration file:
    https://infrastructure.fedoraproject.org/infra/ansible/roles/pkgdb2/templates/pkgdb2.cfg
.. _File a Taskotron ticket:
    https://phab.qadevel.cloud.fedoraproject.org/maniphest/task/edit/form/default/?title=new%20release%20branched&priority=80&tags=libtaskotron
.. _Bodhi SOP: https://infrastructure.fedoraproject.org/infra/docs/bodhi.rst
.. _spin: http://spins.fedoraproject.org
.. _dnf: https://fedoraproject.org/wiki/Dnf
.. _yum: https://fedoraproject.org/wiki/Yum
.. _spin-kickstarts: https://pagure.io/fedora-kickstarts/
.. _file a rel-eng ticket:
    https://fedorahosted.org/rel-eng/newticket?summary=Update%20nightly%20spin%20kickstart&type=task&component=production&priority=critical&milestone=Hot%20issues&cc=kevin
