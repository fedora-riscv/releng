.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
Requesting Automation Users
===========================

.. _sop_requesting_task_automation_user:

Description
===========

When performing automated Release Engineering tasks using :ref:`RelEng
Automation <_releng-automation>` you will sometimes find that you need to
perform an action in the Infrastructure with ``sudo`` that does not yet have
an automation user associated with it.

Actions
========

Requesting a new loopabull_ user
--------------------------------

File a ticket with `Fedora Infrastructure
<https://pagure.io/fedora-infrastructure/>`_ making sure to satisfy the
following requirements:


* Provide a justification for these permissions being needed (What are you
  trying to do and why?)
* Commands needing to be run with sudo
* Destination server on which the commands need to be run
* The ``loopabull_`` username requested to be created for this OR which
  ``loopabull_`` username needs it's pre-existing permissions enhanced

For reference: `Example Infrastructure Ticket
<https://pagure.io/fedora-infrastructure/issue/5943>`_


