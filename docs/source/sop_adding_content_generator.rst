.. SPDX-License-Identifier:    CC-BY-SA-3.0

=================================
Adding new koji content generator
=================================

Description
===========
Koji added support for content generators some time ago. Basic premise of
content generators is that it lets us create build systems for new types of
content without affecting or changing core Koji code and in some way simplify
integration with rest of the release toolchain. More information about content
generators, background, requirements and more can be found in Koji `content
generator documentation`_

For content generator to be able to create/import builds into Koji following
prerequisites have to be met:

* Koji has to recognize the content generator type
* User doing the content generator import has to have permissions for this
  action
* Any new content types have to be defined in Koji

Questions to ask
================
There are some questions that should be answered before the content generator is
enabled/added to Koji

* Where is the content generator service running, what is its support status
  etc?
* Is new type of content being added or is the content generator providing
  different way to build content Koji already knows about?
* What is the expected size of content that will be imported into Koji?
* Does the content generator follow each of the requirements for writing it from
  Koji documentation referenced above?


Adding a new content generator into koji
========================================

First we create the content generator and give a user permission to do imports
for it:

:: 
    
    koji grant-cg-access <username> <content_generator_name> --new

In many cases the content generator will be adding content with new content
type. This can be achieved simply by running:

::

    koji call addBType <content type>


Explanation
-----------
* username - is a name of user which will be doing the imports. In most cases
  this will be a service-level account
* content generator name - this name has to be provided by the content generator
  development team
* --new - this switch ensures we create the content generator if it doesn't
  exist


.. _content generator documentation: https://docs.pagure.org/koji/content_generators/
