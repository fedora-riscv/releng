.. SPDX-License-Identifier:    CC-BY-SA-3.0

=================================
Fedora RelEng Workflow Automation
=================================

.. `releng-automation`_:

The Fedora RelEng Workflow Automation is a means to allow RelEng to define a
pattern by which Release Engineering work is automated in an uniform fashion.
The automation technology of choice is `ansible`_ and the "workflow engine" is
powered by `loopabull`_, which is an event loop that allows us to pass the
information contained within a `fedmsg`_ and insert it into `ansible`_
`playbooks`_. This will effectively create an event driven workflow
that can take action conditionally based on the contents of arbitrary `fedmsg`_
data.

Background on the topic can be found in the `Release Engineering Automation
Workflow Engine`_ Change proposal, as well as in the `releng-automation`_ pagure
repository.

RelEng Workflow Automation Architecture
=======================================

By using `fedmsg`_ as the source of information feeding the event loop, we will
configure `loopabull`_ to listen for specific `fedmsg topics`_ which will
correspond with `ansible`_ `playbooks`_. When one of the appropriate `fedmsg
topics`_ is encountered across the message bus, it's message payload is then
injected into the corresponding playbook as an extra set of variables. A member
of the Fedora Release Engineering Team can at that point use this as a means to
perform whatever arbitrary action or series of actions they can otherwise
perform with `ansible`_ (including what we can enable via custom `modules`_)
based on the input of the message payload.


The general overview of the architecture is below as well as a description of
how it works:

::

                        +------------+
                        |   fedmsg   |
                        |            |
                        +---+--------+
                            | ^
                            | |
                            | |
                            | |
                            | |
                            | |
                            V |
           +------------------+-----------------+
           |                                    |
           |      Release Engineering           |
           |      Workflow Automation Engine    |
           |                                    |
           |      - RabbitMQ                    |
           |      - fedmsg-rabbitmq-serializer  |
           |      - loopabull                   |
           |                                    |
           +----------------+-------------------+
                            |
                            |
                            |
                            |
                            V
                +-----------------------+
                |                       |
                | composer/bodhi/etc    |
                |                       |
                +-----------------------+

The flow of data will begin with an event somewhere in the `Fedora
Infrastructure`_ that sends a `fedmsg`_ across the message bus, then the
messages will be taken in and serialized in to a `rabbitmq`_ worker queue using
`fedmsg-rabbitmq-serializer`_. Then `loopabull`_ will be listening to the
rabbitmq worker queue for tasks to come in. Once a message is recieved, it is
processed and once it is either no-op'd or a corresponding ansible playbook is
run to completion, the message will be ``ack``'d and cleared from the worker
queue. This will allow for us to scale loopabull instances independently from
the message queue as well as ensure that work is not lost because of a downed or
busy loopabull instance. Also, as a point of note, the loopabull service
instances will be scaled using `systemd`_ `unit templates`_.

Once a playbook has been triggered, it will run tasks on remote systems on
behalf of a loopabull automation user. These users can be privileged if need be,
however the scope of their privilege is based on the purpose they serve. These
user accounts are provisioned by the `Fedora Infrastructure`_ Team based on the
requirements of the :ref:`RelEng Task Automation User Request Standard Operating
Procedure (SOP) <sop_requesting_task_automation_user>` document and tasks are
subject to code and security audit.

Fedora Lib RelEng
=================

`Fedora Lib RelEng`_ (flr), is a library and set of command line tools to expose
the library that aims to provide re-usable code for common tasks that need to be
done in Release Engineering. Combining this set of command line tools when
necessary with the Release Engineering Automation pipeline allows for easy
separation of permissions and responsibilities via sudo permissions on remote
hosts. This is explained in more detail on the project's pagure page.

.. _ansible: https://ansible.com/
.. _rabbitmq: https://www.rabbitmq.com/
.. _fedmsg: http://www.fedmsg.com/en/latest/
.. _Fedora Lib RelEng: https://pagure.io/flr
.. _loopabull: https://github.com/maxamillion/loopabull
.. _releng-automation: https://pagure.io/releng-automation
.. _modules: https://docs.ansible.com/ansible/modules.html
.. _systemd: https://freedesktop.org/wiki/Software/systemd/
.. _playbooks: https://docs.ansible.com/ansible/playbooks.html
.. _Fedora Infrastructure: https://fedoraproject.org/wiki/Infrastructure
.. _unit templates: https://fedoramagazine.org/systemd-template-unit-files/
.. _fedmsg-rabbitmq-serializer: https://pagure.io/fedmsg-rabbitmq-serializer
.. _fedmsg topics: https://fedora-fedmsg.readthedocs.io/en/latest/topics.html
.. _Release Engineering Automation Workflow Engine:
    https://fedoraproject.org/wiki/Changes/ReleaseEngineeringAutomationWorkflowEngine
.. _RelEng Automation Request Standard Operating Procedure (SOP): FIXME_WRITE_THIS_DAMN_DOC
