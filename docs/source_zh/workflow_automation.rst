.. SPDX-License-Identifier:    CC-BY-SA-3.0

=================================
Fedora RelEng 工作流程自动化
=================================

.. `releng-automation`_:

Fedora RelEng 工作流自动化是一种允许 RelEng 定义统一方式自动化 Release Engineering 工作的手段。选择的自动化技术是 `ansible`_ ，而
“工作流引擎”由 `loopabull`_ 提供支持，它是一个事件循环，允许我们将包含在 `fedmsg`_ 中的信息传递并插入到 `ansible`_ `playbooks`_ 中。
这将有效地创建一个基于事件驱动的工作流程，可以根据任意 `fedmsg`_ 数据的内容有条件地采取行动。

有关该主题的背景信息可以在“ `Release Engineering Automation
Workflow Engine`_  Change proposal”，以及 `releng-automation`_ pagure 存储库中找到。

RelEng 工作流程自动化的架构
=======================================

通过使用 `fedmsg`_ 作为信息源来提供事件循环，我们将配置 `loopabull`_ 以侦听特定的 `fedmsg 主题`_ ，这些主题将与 `ansible`_ `playbooks`_ 相对应。
当消息总线上遇到适当的 `fedmsg 主题`_ 之一时，它的消息负载将注入到相应的 playbook 中，作为额外的变量集。Fedora Release Engineering 团队的成员可以利
用这一点，根据消息负载的输入执行他们可以使用 `ansible`_ 执行的任意操作或系列操作（包括我们可以通过自定义 `模块`_ 启用的操作）。

下面是架构的概述以及其工作原理的描述：

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

数据流程始于 `Fedora 基础设施`_ 中的某个事件，该事件会通过消息总线发送一个 `fedmsg`_ 。然后使用 `fedmsg-rabbitmq-serializer`_ 将
消息序列化成 `rabbitmq`_ 工作队列。然后 `loopabull`_ 将监听 RabbitMQ 工作队列以等待任务进入。一旦接收到消息，就会处理消息，并且一旦
没有操作或相应的 ansible playbook 完成运行，就会 ``ack`` 并从工作队列中清除消息。这将允许我们独立扩展 loopabull 实例，而不影响消息队列，
并确保由于 downed 或忙碌的 loopabull 实例而不会丢失工作。值得注意的是，loopabull 服务实例将使用 `systemd`_ `unit templates`_ 进行扩展。

一旦触发了 playbook，它将代表 loopabull 自动化用户在远程系统上运行任务。如果需要，这些用户可以拥有特权，但他们的权限范围基于他们所服务的目的。
这些用户帐户由 `fedora 基础设施`_ 团队根据 :ref:`RelEng 任务自动化用户请求标准操作程序（SOP） <sop_requesting_task_automation_user>` 文档的要求进行配置，并且任务受到代码和安全审计的限制。


Fedora Lib RelEng
=================

`Fedora Lib RelEng`_ (flr) 是一个库和一组命令行工具，旨在提供可重用代码，以执行 Release Engineering 中需要完成的常见任务。将这组命令行工具与 Release Engineering 自动化流程结合使用，可以通过远程主机上的 sudo 权限轻松分离权限和责任。有关该项目的详细信息，请参阅项目的 Pagure 页面。

.. _ansible: https://ansible.com/
.. _rabbitmq: https://www.rabbitmq.com/
.. _fedmsg: http://www.fedmsg.com/en/latest/
.. _Fedora Lib RelEng: https://pagure.io/flr
.. _loopabull: https://github.com/maxamillion/loopabull
.. _releng-automation: https://pagure.io/releng-automation
.. _模块: https://docs.ansible.com/ansible/modules.html
.. _systemd: https://freedesktop.org/wiki/Software/systemd/
.. _playbooks: https://docs.ansible.com/ansible/playbooks.html
.. _fedora 基础设施: https://fedoraproject.org/wiki/Infrastructure
.. _unit templates: https://fedoramagazine.org/systemd-template-unit-files/
.. _fedmsg-rabbitmq-serializer: https://pagure.io/fedmsg-rabbitmq-serializer
.. _fedmsg 主题: https://fedora-fedmsg.readthedocs.io/en/latest/topics.html
.. _Release Engineering Automation Workflow Engine:
    https://fedoraproject.org/wiki/Changes/ReleaseEngineeringAutomationWorkflowEngine
.. _RelEng Automation Request Standard Operating Procedure (SOP): FIXME_WRITE_THIS_DAMN_DOC
