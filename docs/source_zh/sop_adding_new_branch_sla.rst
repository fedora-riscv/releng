.. SPDX-License-Identifier:    CC-BY-SA-3.0


================
添加新的分支SLAs
================

说明
====

在ArbitraryBranching模型中，打包者可以为其包的分支选择他们想要的任何SLA，但他们必须从PDC中存储的预定义SLA的子集中进行选择，该子集由reling维护。

本SOP描述了发布工程师创建新SLA所需的步骤。

操作
====

添加新的SLA很简单。它包括使用授权令牌运行releng仓库中的一个脚本。 `pdc-backend01` 上的 `/etc/pdc.d/` 目录中有一个可用的令牌。


::

    $ ./scripts/pdc/insert-sla.py
    Name of the SLA:  wild_and_cavalier
    Description of the SLA:  Anything goes!  This branch may rebase at any time.  No stability guarantees provided.

验证
====

验证SLA是否存在很简单：访问 `对应的PDC端点 <https://pdc.fedoraproject.org/rest_api/v1/component-branch-slas/>`_ 并验证您新添加的SLA是否存在。
