.. SPDX-License-Identifier:    CC-BY-SA-3.0


======================================
Adding a package to a Release Artifact
======================================

Description
===========
In the event that a Fedora contributor would like to have a package added to an
Artifact of a Compose (such as an installer ISO image, a liveCD, Cloud Image,
Vagrant, Docker, etc.) that is slated for Release, the following procedures must
be followed due to the interdependence of different components within the distro
layout.

Background
----------
First, some information on where this all comes from and how things fit
together.

There is the concept of the "Install Tree" which is the collection of packages
available at install time. This is a vast sub-set of the whole of the Fedora
Package Collection and it is the pool of possible packages that is available to
end users who choose to customize their install from the `Anaconda`_ installer.
It is also the pool of possible packages that is available to the
`spin-kickstarts`_ kickstart files that are used to generate various components
of the compose via `pungi`_ which then produces the Release Artifacts.

The Install Tree itself is defined by the `comps`_ groups so in order to add a
net new package to one of the Release Artifacts, the package must be placed in
an appropriate `comps`_ xml file. For more information on what specifically
defines the "appropriate `comps_` xml file" and what kinds of approvals or
review might be needed for adding new packages, please see `this HowTo`_.

Action
======

We will need to edit the comps file specific to the Fedora release we would like
to target. For example, if we were to target Fedora 25 we would edit
``comps-f25.xml.in`` found within the `comps`_ git repository and this should be
modified based on the `How to edit comps`_ procedure.

If the package that was added is a part of a pre-existing comps group that is
already used in the target Release Artifact's `spin-kickstarts`_ kickstart file
then we are done.

However, if there is a new comps group added then we need to include that new
comps group in the respective `spin-kickstarts`_ kickstart file similar to the
following.

::

    %packages
    @mynewcompsgroup


Next we will need to tell `pungi`_ Variants data about the new group and it's
relationship to the corresponding `Variant`_. This information is held in the
`Fedora Pungi Configs`_ `pagure`_ git forge repository. The file needed to be
edited is ``variants-fedora.xml`` and can be viewed from a web browser `here`_.

Once this has been completed, we're all done.

Verification
============

Verify that the next compose is successful and that the change made didn't cause
any issues. This can be done from the `Fedora Product Definition Center`_ which
is a central store of information about Composes and their resulting artifacts.

Consider Before Running
=======================
.. Create a list of things to keep in mind when performing action.

.. _pagure: https://pagure.io/
.. _pungi: https://pagure.io/pungi
.. _comps: https://fedorahosted.org/comps/
.. _Anaconda: https://fedoraproject.org/wiki/Anaconda
.. _Fedora Pungi Configs: https://pagure.io/pungi-fedora
.. _spin-kickstarts: https://fedorahosted.org/spin-kickstarts/
.. _here: https://pagure.io/pungi-fedora/blob/master/f/variants-fedora.xml
.. _Fedora Product Definition Center: https://pdc.fedoraproject.org/compose/
.. _this HowTo:
    https://fedoraproject.org/wiki/How_to_use_and_edit_comps.xml_for_package_groups
.. _Variant:
    https://sgallagh.wordpress.com/2016/03/18/sausage-factory-multiple-edition-handling-in-fedora/
.. _How to edit comps:
    https://fedoraproject.org/wiki/How_to_use_and_edit_comps.xml_for_package_groups#How_to_edit_comps
