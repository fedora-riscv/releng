"""
This script is useful to bulk orphan listed packages.
E.g. when they fail to install or fail to build.
"""

import logging
import os
import sys

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

REASON = "Important bug not fixed"
# REASON = "Fails to build from source"
# REASON = "Orphaned by releng"

PACKAGES = {
    # "pkg_name": "https://bugzilla.redhat.com/XXX or a different info",
}

PAGURE_TOKEN = os.getenv("PAGURE_TOKEN")
LOG = logging.getLogger(__name__)
BASE_URL = "https://src.fedoraproject.org"


def retry_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=0.3,
        status_forcelist=(500, 502, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def orphan_package(name, namespace="rpms", reason=REASON, reason_info=None):
    """Give the specified project on dist_git to the ``orphan`` user."""
    LOG.debug("Going to orphan: %s/%s", namespace, name)
    session = retry_session()

    # Orphan the package
    url = f"{BASE_URL}/_dg/orphan/{namespace}/{name}"
    headers = {"Authorization": f"token {PAGURE_TOKEN}"}
    data = {
        "orphan_reason": reason,
    }
    if reason:
        data["orphan_reason_info"] = reason_info

    req = session.post(url, data=data, headers=headers)
    if not req.ok:
        print("**** REQUEST FAILED")
        print("  - Orphan package")
        print(req.url)
        print(data)
        print(headers)
        print(req.text)
    else:
        print(f"{namespace}/{name} is orphaned")

    session.close()


def get_bugzilla_overrides(name, namespace="rpms"):
    """Returns bugzilla overrides of the specified package.. """
    LOG.debug("Checking for bugzilla overrides on %s/%s", namespace, name)
    session = retry_session()
    req = session.get(f"{BASE_URL}/_dg/bzoverrides/{namespace}/{name}")
    return req.json()


def reset_bugzilla_overrides(name, namespace="rpms"):
    """ Reset the Fedora bugzilla overrides of the specified package."""
    overrides = get_bugzilla_overrides(name)

    if overrides["fedora_assignee"] is None:
        LOG.debug("No bugzilla overrides on %s/%s", namespace, name)
        return

    LOG.debug("Resetting bugzilla overrides on %s/%s", namespace, name)
    url = f"{BASE_URL}/_dg/bzoverrides/{namespace}/{name}"
    headers = {"Authorization": f"token {PAGURE_TOKEN}"}

    username = overrides["fedora_assignee"]
    overrides["fedora_assignee"] = None

    session = retry_session()
    req = session.post(url, headers=headers, data=overrides)
    if not req.ok:
        print("**** REQUEST FAILED")
        print("  - Remove bugzilla overrides")
        print(req.url)
        print(req.text)
    else:
        print(f"  {username} has no longer a bugzilla overrides on {namespace}/{name}")
    session.close()


if __name__ == "__main__":
    if not PACKAGES:
        sys.exit("Define PACKAGES first")

    for package in PACKAGES:
        orphan_package(package, reason_info=PACKAGES[package])
        reset_bugzilla_overrides(package)
