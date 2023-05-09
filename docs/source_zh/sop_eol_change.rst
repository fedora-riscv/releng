.. SPDX-License-Identifier:    CC-BY-SA-3.0

================================
调整分支上的EOL和SL
================================

.. note:: 本SOP是关于调整所谓“任意”分支上的EOL和SL。撤消包 *还* 需要更改分支上的EOL，但您在此处找不到有关这方面的信息。有关更多信息请参阅取消退役SOP。

说明
===========

通过“任意分支”，模块可以包含与Fedora版本没有直接关联的RPM流。模块 *本身* 可以具有与Fedora版本没有直接关联的分支。例如，我们的
`python3` 模块有一个 `3.6` 分支。该模块分支上的SL将于2018-06-01全部下线。 **@torsava** ， `python3模块维护者
<https://src.fedoraproject.org/modules/python3k>`_ 之一, 可能会请求将该分支的EOL扩展到2018-12-01。

当维护人员想要更改rpm、模块或容器分支的EOL时，他们需要提交一个 `releng ticket <https://pagure.io/releng/issues>`_
来请求。他们没有办法独自完成。Releng必须审查请求，然后进行处理。

政策
======

以下是一些 *政策* 指南，可以帮助您（releng）对这些工单做出决定

- 澄清维修人员是否希望EOL延长一转/分？还是模块？还是集装箱？如果他们只是说“请增加 `httpd` 的EOL”，那么他们到底在说什么还不清楚。

- 通常来说维护者会知道他们的软件包 *何时* 应该结束生命周期。你不需要去研究上游邮件列表以确定哪个时间点最合适。
  礼貌地向维护者询问更改 EOL 的背景信息，并将记录保存在工单中，是好的做法，这样对于后人来说也很有价值。如果维护者能够提供上游讨论的参考资料，以便更好地理解请求的合理性，则更加优秀。

- EOL *几乎总是* 只能向将来延长，缩短EOL应该谨慎进行。可能存在依赖于其自己 EOL 产生冲突的 rpm 分支的模块。如果要请求缩短 rpm 分支 EOL，应验证没有依赖它的有冲突 EOL 的模块。如果要请求缩短模块分支的EOL，您应验证没有其他模块需要它们并且有冲突的EOL。

- EOL不应为任意日期。在Flock 2017上，我们 `决定使用两个标准的EOL日期 <https://pagure.io/fedrepo_req/issue/100>`_ 以使事情变得更合理。您应该使用任何一年的12月1日或6月1日作为所有EOL日期。

- 许多分支 *通常* 会有多个SL，这些SL在EOL方面都是 *一样* 的。 即，该分支在完全退役之前都得到了充分支持，没有灰色地带。但是， *可能* 会有分支具有零散的SL和EOL。一个分支可能支持 `bug_fixes` 直到时间 X，但将进一步支持 `security_fixes` 直到时间 Y。
  这对于维护者来说非常灵活，但也引入了复杂性。如果维护者请求零散的SL EOL，请询问以确保他们确实需要这种复杂性。

操作
======

我们在 releng repo中有一个脚本::

    $ PYTHONPATH=scripts/pdc python3 scripts/pdc/adjust-eol.py -h

.. note:: 和 `python3`一起运行。它默认情况下导入python3的 `fedrepo_req`。需要时可以安装python2依赖项。

以下是使用它来增加 `python3` 模块 `3.6` 分支 (而不是rpm分支)的SL的示例::

    $ PYTHONPATH=scripts/pdc python3 scripts/pdc/adjust-eol.py \
        fedora \
        SOME_TOKEN \
        python3 \
        module \
        3.6 \
        2018-12-01
    Connecting to PDC args.server 'fedora' with token 'a9a1e4cbca122c21580d1fe4646e603a770c5280'
    Found 2 existing SLs in PDC.
    Adjust eol of (module)python3#3.6 security_fixes:2018-06-01 to 2018-12-01? [y/N]: y
    Adjust eol of (module)python3#3.6 bug_fixes:2018-06-01 to 2018-12-01? [y/N]: y
    Set eol to 2018-12-01 on ['(module)python3#3.6 security_fixes:2018-06-01', '(module)python3#3.6 bug_fixes:2018-06-01']
