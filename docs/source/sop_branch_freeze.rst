.. SPDX-License-Identifier:    CC-BY-SA-3.0


================
Branching Freeze
================


Introduction/Background
=======================

When the next release is branched from rawhide, it initially composes much
like rawhide with nightly composes and no updates process.

Once the Bodhi is activated, we will push updates to the branched and the
nightly composes will start to differ. But two weeks before the scheduled
release of either Beta or GA, we will start the freeze for that release and
stop pushing updates.

* Send announcement to devel-announce mailing list noting that the alpha
  change freeze is going to happen at least one day in advance.

.. note::
    For updates pushers:
        In Change freeze only updates that fix accepted blockers or Freeze
        break bugs are allowed into the main tree. Please coordinate with QA
        for any stable updates pushes. Otherwise ONLY push updates-testing.

.. note::
    For Final/GA release:
        During Final freeze, we dont want to block any packages in koji as
        it will effect the RC composes. So, please update the block_retired.py_
        script and remove the branched release reference.

.. _block_retired.py: https://pagure.io/releng/blob/master/f/scripts/block_retired.py
