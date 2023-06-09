.. SPDX-License-Identifier:    CC-BY-SA-3.0

===================================
Process fedora-scm-requests tickets
===================================

Description
===========

When a packager wants a new package added to Fedora or a new dist-git branch
blessed, they need to go through the new package process and, once their
package review is approved, they use the `fedrepo-req` cli tool to file a
ticket in the `fedora-scm-requests queue
<https://pagure.io/releng/fedora-scm-requests>`_.

Periodically, (daily?) release engineering will need to review and process this
queue using the `fedrepo-req-admin` tool.

Setup
=====

A release engineering will need to have several values set locally as well as
sufficient permissions in a number of server-side systems.

#. A pagure.io token.  See the fedrepo-req README for instructions on where to get this.
#. src.fedoraproject.org token generated by `pagure-admin`.  Ask @pingou how to get one.
   If doing this yourself, go to pkgs01 and run
   `PAGURE_CONFIG=/etc/pagure/pagure.cfg pagure-admin admin-token create -h`
   for more info.
#. pdc token.  See the PDC SOP for getting one of these.

Action
======

#. Run `fedrepo-req-admin list` to list all open requests.
#. Run `fedrepo-req-admin process N` to process a particular ticket.
#. Run `fedrepo-req-admin processall` to iterate over all the tickets.
