# Fedora Product Definition Center

## Install fpdc-client

Currently fpdc-client is only available on PyPI, so to use the scripts in this folder you need to use a virtual environment.

    $ python3 -m venv venv
    $ source venv/bin/active
    (venv) $ pip install fpdc-client

## Add a new release in fpdc

To add a new release in fpdc you can use the provided `create-new-release.py` script.

    (venv) $ python scripts/fpdc/create-new-release.py --releaseid fedora-28 --version 28 --release-date 2018-05-01 --eol-date 2019-06-01 --sigkey test

The script has a flag to use the staging server for testing.

    (venv) $ python scripts/fpdc/create-new-release.py --staging --releaseid fedora-28 --version 28 --release-date 2018-05-01 --eol-date 2019-06-01 --sigkey test


## Authentication and Permissions

fpdc is using FAS for authentication, when executing the script, you will be asked to login in the web browser using your FAS credentials.

Once logged in fpdc will make sure that you have the correct permissions, currently members of the `releng-team` group are allowed to create/update/delete releases.

## Deactivate the virtual environment

When you are done you can leave the virtual environment.

    (venv) $ deactivate
