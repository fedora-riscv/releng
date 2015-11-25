.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
Update RelEng Rendered Docs
===========================

Description
===========
.. Put a description of the task here.

When an improvement happens to the Release Engineering documentation following
the :doc:`contributing <contributing>` for the `Sphinx`_ `reStructured Text`_
source found in ``docs/source`` within the `RelEng git repository`_ someone has
to manually perform a process in order to update the documentation that is
hosted in the `pagure`_ documentation space for `Fedora RelEng docs`_.

Action
======
.. Describe the action and provide examples

In order to render the documentation using `Sphinx`_, you need to first be sure
to have the package installed:

::

    $ dnf install python-sphinx

Then we'll need to clone the RelEng repository and the RelEng docs repository
(the docs git repository is provided by pagure automatically). We could
alternatively use an already cloned local git checkout of the `releng`
repository but it is recommended to use a clean clone just to make sure changes
or build artifacts from previous html renderings don't make it into the live
documentation site.

::

    $ git clone https://pagure.io/releng.git /tmp/releng
    $ cd /tmp/releng/docs
    $ make html

    $ git clone ssh://git@pagure.io/docs/releng.git /tmp/releng-doc
    $ cd /tmp/releng-doc
    $ git rm -fr ./*
    $ cp -r /tmp/releng/docs/build/html/* ./
    $ git add .
    $ git commit -m "update rendered releng docs"
    $ git push origin master

The documentation is now live and these local clones of the remote git
repositories can be safely removed.

.. note::
    This will require someone with permissions to push to the master branch for
    the releng repository. If you are curious whom all has this ability, please
    refer to the :doc:`Main Page <index>` and contact someone from the "Team
    Composition"

Verification
============
.. Provide a method to verify that the action completed as expected (success)

Visit the `Fedora RelEng docs`_ website and verify that the changes are
reflected live on the docs site.

Consider Before Running
=======================
.. Create a list of things to keep in mind when performing action.

No considerations at this time. The docs git repository is simply a static
html hosting space and we can just re-render the docs and push to it again if
necessary.

.. _Sphinx: http://sphinx-doc.org/
.. _reStructured Text: https://en.wikipedia.org/wiki/ReStructuredText
.. _RelEng git repository: https://pagure.io/releng
.. _pagure: https://pagure.io/pagure
.. _Fedora RelEng docs: https://docs.pagure.org/releng/
