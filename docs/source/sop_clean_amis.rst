.. SPDX-License-Identifier:    CC-BY-SA-3.0

==================
Clean AMIs Process
==================

Description
===========

The Fedora AMIs are uploaded on a daily basis to Amazon Web Services. Over time
the number of AMIs piles up and have to be removed manually. Manual removal comes
with it's own set of issues where missing to delete the AMIs is a viable issue.

The goal of the script is to automate the process and continue regular removal of
the AMIs. The report of the script is pushed to a `Pagure repo`_

Action
======

There is a script in the `Fedora RelEng repo`_ named ``clean-amis.py`` under
the ``scripts`` directory.

The script runs as a cron job within the Fedora Infrastructure to delete
the old AMIs. The permission of the selected AMIs are changed to private.
This is to make sure that if someone from the community raises an issue
we have the option to get the AMI back to public.
After 10 days, if no complaints are raised the AMIs are deleted permanently.

The complete process can be divided in couple of parts:

- Fetching the data from datagrepper.
  Based on the `--days` param, the script starts fetching the fedmsg messages
  from datagrepper for the specified timeframe i.e. for lasts `n` days, where
  `n` is the value of `--days` param. The queried fedmsg
  topic `fedimg.image.upload`.

- Selection of the AMIs:
  After the AMIs are parsed from datagrepper. The AMIs are filtered to remove
  Beta, Two-week Atomic Host and GA released AMIs.
  Composes with `compose_type` set to `nightly` are picked up for deletion.
  Composes which contain date in the `compose label` are also picked up for
  deletion.
  GA composes also have the compose_type set to production. So to distinguish
  then we filter them if the compose_label have date in them. The GA
  composes dont have date whereas they have the version in format of X.Y

- Updated permissions of AMIs
  The permissions of the selected AMIs are changed to private.

- Deletion of AMIs
  After 10 days, the private AMIs are deleted.

In order to change the permissions of the AMIs use the command given below, add
`--dry-run` argument test the command works. Adding `--dry-run` argument will
print the AMIs to console.

::

   AWS_ACCESS_KEY={{ ec2_image_delete_access_key_id }} AWS_SECRET_ACCESS_KEY={{ ec2_image_delete_access_key }} PAGURE_ACCESS_TOKEN={{ ami_purge_report_api_key }} ./clean-amis.py --change-perms --days 7 --permswaitperiod 5


In order to delete the AMIs whose launch permissions have been removed, add
`--dry-run` argument test the command works. Adding `--dry-run` argument will
print the AMIs to console.

::

   AWS_ACCESS_KEY={{ ec2_image_delete_access_key_id }} AWS_SECRET_ACCESS_KEY={{ ec2_image_delete_access_key }} PAGURE_ACCESS_TOKEN={{ ami_purge_report_api_key }} ./clean-amis.py --delete --days 17 --deletewaitperiod 10


.. _Pagure repo: https://pagure.io/ami-purge-report
.. _Fedora RelEng repo: https://pagure.io/releng
