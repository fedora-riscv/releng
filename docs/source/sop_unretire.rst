.. SPDX-License-Identifier:    CC-BY-SA-3.0


===========================
Unretiring a package branch
===========================

Description
===========

Sometimes, packagers request that we *unretire* a package branch that has
previously been retired.

This typically happens on the `rawhide` branch, but could conceivably happen on
any stable or arbitrary branch.

Action
======

Validate Package Ready for Unretirement
---------------------------------------
#. Verify the package was not retired for any reason, such as legal or
   license issues, that would prevent it from being re-instated.

#. Ensure a bugzilla was filed to review the package for unretirement.

#. Verify with the the requestor exactly which tags they would like
   unblocked as part of the unretirement request.

Revert the Retirement Commit
----------------------------
#. Connect to one of the compose systems.

    ::

    $ ssh compose-x86-02.phx2.fedoraproject.org

#. Clone the git-dist package using the the proper release engineering
   credentials.

    ::

    $ GIT_SSH=/usr/local/bin/relengpush fedpkg --user releng clone PACKAGENAME

#. Enter the directory of the cloned package and configure the git user
   information.

    ::

    $ cd PACKAGENAME
    $ git config --local user.name "Fedora Release Engineering"
    $ git config --local user.email "releng@fedoraproject.org"

#. Git revert the `dead.package` file commit in dist-git on the particular branch
   using its commit hash_id. Ensure the commit message contains a URL to the
   request in pagure.

    ::

    $ git revert -s COMMIT_HASH_ID
    $ GIT_SSH=/usr/loca/bin/relengpush fedpkg --user releng push

Unblock the Package in Koji
---------------------------

#. Check the current state of the branches in koji for the package.

    ::

    $ koji list-pkgs --show-blocked --package=PACKAGENAME

#. Unblock each requested tag using koji.

   ::

    $ koji unblock-pkg TAGNAME PACKAGENAME

Verify Package is Not Orphaned
------------------------------

#. Check package ownership

   Navigate to `https://src.fedoraproject.org/` and check package owner.

#. If the package is orphaned, then give the package to the requestor using
   the `give-package` script from the `Release Engineering Repo`_.

   ::

   $ ./scripts/distgit/give-package --package=PACKAGENAME --custodian=REQUESTOR

   .. note::
       This script requires the user to be a member of the group `cvsadmin`
       in FAS.

Update Product Definition Center (PDC)
-----------------------------------------

.. note::
    If there are more than one tag to be unblocked then the PDC update
    step should be completed for each tag and package.

#. Log into the `Fedora PDC instance`_ using a FAS account.

#. Check PDC for the entry for the `PACKAGENAME` in each `TAG` that was
   unblocked in a previous step.

    ::

    https://pdc.fedoraproject.org/rest_api/v1/component-branch-slas/?branch=TAG&global_component=PACKAGENAME

    .. note::
         If no information is returned by this query then it is not in PDC
         and is likely not yet a branch. The requestor should use the
         `fedpkg request-branch` utility to ask for a branch.

#. If the package existed within PDC then obtain a token from the PDC site
   while logged in by navigating to the
   `https://pdc.fedoraproject.org/rest_api/v1/auth/token/obtain/` URL with
   the Firefox web browser.

#. Press F12 once the page has loaded and select the tab labeled `Network`.
   Refresh the web page and find the line whose string in the file column
   matches `/rest_api/v1/auth/token/obtain/`.

#. Right click on specified line and select Copy>Copy as cURL.  Paste this
   into a terminal session and add `-H "Accept: application/json"`. It should look
   something similar to the below:

    ::

        $ curl 'https://pdc.fedoraproject.org/rest_api/v1/auth/token/obtain/' \
        -H 'Host: pdc.fedoraproject.org' \
        -H .0) Gecko/20100101 Firefox/57.0' \
        -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
        -H 'Accept-Language: en-US,en;q=0.5' \
        --compressed \
        -H 'Cookie: csrftoken=CSRF_TOKEN_HASH; SERVERID=pdc-web01; mellon-saml-sesion-cookie=SAML_SESSION_HASH; sessionid=SESSION_ID_HASH' \
        -H 'Connection: keep-alive' \
        -H 'Upgrade-Insecure-Requests: 1' \
        -H 'Cache-Control: max-age=0' \
        -H "Accept: application/json"

#. Using the token obtained from the previous step run the `adjust-eol.py`
   script from the `Release Engineering Repo`_.

    ::

    $ PYTHONPATH=scripts/pdc/ scripts/pdc/adjust-eol.py fedora MYTOKEN PACKAGENAME rpm TAG default -y

    .. note::
        The local machine will have configuration information in the `/etc/pdc.d/` directory. This is why *fedora* can be passed as an argument instead of the full API endpoint URL.


.. _Fedora PDC instance: https://pdc.fedoraproject.org/
.. _Release Engineering Repo: https://pagure.io/releng
