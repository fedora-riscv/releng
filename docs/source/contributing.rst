.. SPDX-License-Identifier:    CC-BY-SA-3.0

=============================================
Fedora Release Engineering Contributing Guide
=============================================

Fedora Release Engineering works with many different utilities that are
maintained in respective upstream locations. Fedora Release Engineering
maintains an "Upstream First" policy such that if there is a bug in an utility
or a feature needed, we pursue that upstream before entertaining the idea of
carrying a Fedora specific patch.

Fedora Release Engineering also has a number of scripts and utilities that are
strictly Fedora centric in order to automate tasks and processes as they
relate to Fedora itself which is what is contained in the `releng git
repository`_ hosted on `Pagure`_. If you would like to contribute to something
in this repository, please reference the :ref:`contributing-to-releng` section.

.. _contributing-to-releng:

Contributing to releng
======================

In order to contribute to the releng `git`_ repository (where the source
reStructured Text version of these docs live), you should first have a `Fedora
Account System`_ (FAS) account, log into `pagure.io`_ and the fork the `releng
git repository`_.

Once you've forked the `releng git repository`_, you will need to set the remote
upstream git clone of your fork in order to track the official releng
repository. While not mandatory, it's conventional to call the remote upstream
the name ``upstream`` which can be done with the following command while within
the directory of your local git clone of your fork.

.. code:: bash

    $ git remote add upstream https://pagure.io/releng.git

.. note::

    If you are not currently familiar with git, it is highly recommended to
    visit git's upstream and familiarize yourself.

    http://www.git-scm.com/


RelEng Developer Workflow
-------------------------

There are many options for developer workflow, but the recommended workflow for
Fedora releng repository is known as a "`Topic Branch`_" based workflow in git
nomenclature. This is how Fedora Release Engineering contributors can submit
changes to the `releng git repository`_ for both code and documentation.

The general workflow is as follows:

* Checkout ``master`` branch of the local git clone of your releng repository
  clone.

  ::

    $ git checkout master

* Pull upstream and merge into local master to make sure that your master
  branch is in line with the latest changes from upstream. Then push it to your
  clone so that origin knows about the changes.

  ::

    $ git pull --rebase upstream master
    $ git push origin master

* Create a topic branch from master.

  ::

    $ git checkout -b my-topic-branch

* Make changes in your topic branch and commit them to your topic branch.

  ::

    $ vim somefile.py

    .... make some change ...

    $ git add somefile.py
    $ git commit -s -m "awesome patch to somefile.py"

* This step is optional but recommended in order to avoid collisions when
  submitting upstream. Here we will checkout master again and merge
  ``upstream/master`` so that we can resolve any conflicts locally.

  ::

    $ git checkout master
    $ git pull --rebase upstream master
    $ git push origin master

* Rebase on master before submitting a pull request

  ::

    $ git rebase master

    ..... Resolve any conflicts if needed ......

* Push your topic branch to your fork's origin in pagure.

  ::

    $ git push origin my-topic-branch


* Open a pull request in Rel Eng Pagure. https://pagure.io/releng/pull-requests



Developer Workflow Tips and Tricks
----------------------------------

Below are some Fedora Release Engineering Developer Workflow Tips and Tricks
used by current members of the team in order to help assist with development.

pullupstream
^^^^^^^^^^^^


The following is an useful shell function to place in your ``~/.bashrc`` to
help automate certain aspects of the developer workflow. It will allow you to
merge in the upstream master or devel branch into your forked repository for
easily keeping in line with the upstream repository.

The following is the bash function to be added to your ``~/.bashrc`` and make
sure to ``source ~/.bashrc`` after adding it in order to "enable" the function.

::

    pullupstream () {
        if [[ -z "$1" ]]; then
            printf "Error: must specify a branch name (e.g. - master, devel)\n"
        else
            pullup_startbranch=$(git describe --contains --all HEAD)
            git checkout $1
            git pull --rebase upstream $1
            git push origin $1
            git checkout ${pullup_startbranch}
        fi
    }

With the function in place you can easily pull and merge in the releng master
branch even while using a topic branch as follows:

::

    $ git status
    On branch docs
    nothing to commit, working directory clean

    $ pullupstream master
    Switched to branch 'master'
    Your branch is up-to-date with 'origin/master'.
    Already up-to-date.
    Everything up-to-date
    Switched to branch 'docs'

    $ git status
    On branch docs
    nothing to commit, working directory clean

Now that you're back on your topic branch you can easily rebase on your local
master branch in order to resolve any merge conflicts that may come up for
clean pull request submission.

::

    $ git rebase master
    Current branch docs is up to date.


RelEng Upstream Tools
=====================

Fedora Release Engineering uses many tools that exist in their own upstream
project space. These are tools that every Fedora Release Engineer should be
familiar with and in the event there is a bug or a feature needed, we should
participate in the respective upstream to resolve the issue first before
considering carrying a Fedora specific patch.

Tools List
----------

Tools Release Engineering is actively involved with upstream
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Below are a set of tools that are centric to the Release Engineering team and
our processes. We actively engage with upstreams of these projects. For these
tools, we recommend the same git contribution workflow that is outlined above
for this git repository.

* `koji <https://pagure.io/koji>`_ -
  Build System used by Fedora
* `mash <https://pagure.io/mash>`_ -
  Tool that creates repositories from koji tags, and solves them for multilib
  dependencies.
* `pungi <https://pagure.io/pungi>`_ -
  Fedora Compose tool
* `Product Defintion Center (PDC)
  <https://github.com/release-engineering/product-definition-center>`_ -
  Repository and API for storing and querying product metadata
* `koji-containerbuild
  <https://github.com/release-engineering/koji-containerbuild>`_ -
  Koji plugin to integrate OSBS with koji

Tools Release Engineering is actively mostly consumers of
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Below are the set of tools that the Release Engineering team either consumes
directly or as the side effect of other tools in the Release Engineering
Infrastructure. Tools here should always be engaged upstream in the event of a
bug or enhancement needed but are not tools that the Release Engineering team
is extremely active in their continued upstream development and will defer to
each upstream for recommended contributions workflow.

* `fedpkg <https://pagure.io/fedpkg>`_ -
  command line utility for Fedora (and EPEL) developers. It interacts with
  dist-git, koji, rpmbuild, git, etc.
* `rpkg <https://pagure.io/rpkg>`_ -
  library for dealing with rpm packaging in a git source control (used by
  fedpkg)
* `dist-git <https://github.com/release-engineering/dist-git>`_ -
  remote Git repository specificaly designed to hold RPM package sources.
* `creatrepo <http://createrepo.baseurl.org/>`_ -
  A python program which generate repodata from a set of rpm files.
* `createrepo_c <https://github.com/rpm-software-management/createrepo_c>`_ -
  C implementation of createrepo
* `oz <https://github.com/clalancette/oz>`_ -
  set of programs and classes to do automated installations of operating
  systems.
* `imagefactory <http://imgfac.org/>`_ -
  imagefactory builds images for a variety of operating system/cloud
  combinations.
* `sigul <https://fedorahosted.org/sigul/>`_ -
  An automated gpg signing system
* `mock <https://fedoraproject.org/wiki/Mock>`_ -
  a tool for building packages in prestine buildroots
* `fedmsg <http://www.fedmsg.com/en/latest/>`_ -
  Fedora Infrastructure Message Bus
* `lorax <https://github.com/rhinstaller/lorax>`_ -
  tool to build install trees and images
* `OpenShift <http://www.openshift.org/>`_ -
  Open Source Platform as a Service by Red Hat
* `OSBS <https://github.com/projectatomic/osbs-client>`_ -
  set of utilities that turn OpenShift into a layered image build system
* `taskotron <https://fedoraproject.org/wiki/Taskotron>`_ -
  a framework for automated task execution.
* `pulp <http://www.pulpproject.org/>`_ -
  a platform for managing repositories of content, such as software packages,
  and pushing that content out to large numbers of consumer
* `crane <https://github.com/pulp/crane>`_ -
  Crane is a small read-only web application that provides enough of the docker
  registry API to support "docker pull"
* `pagure <https://pagure.io/pagure>`_
  A git centered forge
* `rpm-ostree <https://github.com/projectatomic/rpm-ostree>`_ -
  Store RPMs in OSTree repository, and atomically upgrade from commits
* `ostree <https://wiki.gnome.org/Projects/OSTree>`_ -
  a tool for managing bootable, immutable, versioned filesystem trees.

.. _releng git repository: https://pagure.io/releng
.. _Pagure: https://pagure.io/pagure
.. _Fedora Account System: https://admin.fedoraproject.org/accounts
.. _pagure.io: https://pagure.io
.. _Topic Branch: http://www.git-scm.com/book/en/v2/Git-Branching-Branching-Workflows#Topic-Branches
.. _git: http://www.git-scm.com
