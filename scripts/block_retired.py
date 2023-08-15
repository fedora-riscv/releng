#!/usr/bin/python3
# vim: fileencoding=utf8
# SPDX-License-Identifier: GPL-2.0+

import argparse
import getpass
import logging
import subprocess
import time

import koji
import requests


log = logging.getLogger(__name__)
RETIRING_BRANCHES = ["el6", "epel7", "epel8", "epel8-next", "epel9", "epel9-next", "epel8-playground", "rawhide", "f39"]
PROD_ONLY_BRANCHES = ["el6", "epel7", "epel8", "epel8-next", "epel9", "epel9-next", "epel8-playground", "rawhide", "f39"]

PRODUCTION_PDC = "https://pdc.fedoraproject.org"
STAGING_PDC = "https://pdc.stg.fedoraproject.org"

# default namespace
DEFAULT_NS = "rpms"


class SubjectSMTPHandler(logging.handlers.SMTPHandler):

    subject_prefix = ""

    def getSubject(self, record):
        first_line = record.message.split("\n")[0]
        fmt = self.subject_prefix + "{0.levelname}: {first_line}"

        return fmt.format(record, first_line=first_line)


class ReleaseMapper(object):
    BRANCHNAME = 0
    KOJI_TAG = 1
    EPEL_BUILD_TAG = 2

    def __init__(self, staging=False, namespace=DEFAULT_NS):

        if namespace == "container":
            # git branchname, koji tag, epel build tag
            self.mapping = (
                ("rawhide", "f40-container", ""),
                ("f39", "f39-container", ""),
                ("f38", "f38-container", ""),
                ("f37", "f37-container", ""),
                ("f36", "f36-container", ""),
                ("f35", "f35-container", ""),
                ("f34", "f34-container", ""),
                ("f33", "f33-container", ""),
                ("f32", "f32-container", ""),
                ("f31", "f31-container", ""),
                ("f30", "f30-container", ""),
                ("f29", "f29-container", ""),
                ("f28", "f28-container", ""),
                ("f27", "f27-container", ""),
                ("f26", "f26-container", ""),
                ("f25", "f25-container", ""),
            )
        else:
            # git branchname, koji tag, epel build tag
            self.mapping = (
                ("rawhide", "f40", ""),
                ("f39", "f39", ""),
                ("f38", "f38", ""),
                ("f37", "f37", ""),
                ("f36", "f36", ""),
                ("f35", "f35", ""),
                ("f34", "f34", ""),
                ("f33", "f33", ""),
                ("f32", "f32", ""),
                ("f31", "f31", ""),
                ("f30", "f30", ""),
                ("f29", "f29", ""),
                ("f28", "f28", ""),
                ("f27", "f27", ""),
                ("f26", "f26", ""),
                ("f25", "f25", ""),
                ("f24", "f24", ""),
            )

            if not staging:
                self.mapping = self.mapping + (
                    ("epel9", "epel9", "epel9-build"),
                    ("epel9-next", "epel9-next", "epel9-next-build"),
                    ("epel8-playground", "epel8-playground", "epel8-playground-build"),
                    ("epel8", "epel8", "epel8-build"),
                    ("epel8-next", "epel8-next", "epel8-next-build"),
                    ("epel7", "epel7", "epel7-build"),
                    ("el6", "dist-6E-epel", "dist-6E-epel-build"),
                )

    def branchname(self, key=""):
        return self.lookup(key, self.BRANCHNAME)

    def koji_tag(self, key=""):
        return self.lookup(key, self.KOJI_TAG)

    def epel_build_tag(self, key=""):
        return self.lookup(key, self.EPEL_BUILD_TAG)

    def lookup(self, key, column):
        if key:
            key = key.lower()
            for row in self.mapping:
                for c in row:
                    if c.lower() == key:
                        return row[column]
        else:
            return [row[column] for row in self.mapping]
        return None


def get_packages(tag, staging=False):
    """
    Get a list of all blocked and unblocked packages in a branch.
    """
    profile = PRODUCTION_KOJI_PROFILE if not staging else STAGING_KOJI_PROFILE
    koji_module = koji.get_profile_module(profile)
    kojisession = koji_module.ClientSession(koji_module.config.server)
    pkglist = kojisession.listPackages(tagID=tag, inherited=True)
    blocked = []
    unblocked = []

    for p in pkglist:
        pkgname = p["package_name"]
        if p.get("blocked"):
            blocked.append(pkgname)
        else:
            unblocked.append(pkgname)

    return unblocked, blocked


def unblocked_packages(branch="rawhide", staging=False, namespace=DEFAULT_NS):
    """
    Get a list of all unblocked pacakges in a branch.
    """
    mapper = ReleaseMapper(staging=staging, namespace=namespace)
    tag = mapper.koji_tag(branch)
    unblocked, _ = get_packages(tag, staging)
    return unblocked


def get_retired_packages(branch="rawhide", staging=False, namespace=DEFAULT_NS):
    retiredpkgs = []
    # PDC uses singular names such as rpm and container
    if namespace.endswith('s'):
        content_type = namespace[:-1]
    else:
        content_type = namespace
    url = PRODUCTION_PDC if not staging else STAGING_PDC
    url = ('{0}/rest_api/v1/component-branches/?name={1}&type={2}'
           '&active=false&page_size=100'.format(url, branch, content_type))
    while True:
        rv = requests.get(url)
        if not rv.ok:
            raise RuntimeError('Failed getting the retired packages from '
                               'PDC. The response was: {0}'
                               .format(rv.content))

        rv_json = rv.json()
        for branch in rv_json['results']:
            retiredpkgs.append(branch['global_component'])

        if rv_json['next']:
            url = rv_json['next']
        else:
            break

    return retiredpkgs


def run_koji(koji_params, staging=False):
    profile = PRODUCTION_KOJI_PROFILE if not staging else STAGING_KOJI_PROFILE
    koji_cmd = ["koji", "--profile", profile]
    cmd = koji_cmd + koji_params
    log.debug("Running: %s", " ".join(cmd))
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                               stdout=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return process, stdout, stderr


def block_package(packages, branch="rawhide", staging=False, namespace=DEFAULT_NS):
    if isinstance(packages, str):
        packages = [packages]

    if len(packages) == 0:
        return None

    mapper = ReleaseMapper(staging=staging, namespace=namespace)
    tag = mapper.koji_tag(branch)
    epel_build_tag = mapper.epel_build_tag(branch)

    errors = []

    def catch_koji_errors(cmd):
        process, stdout, stderr = run_koji(cmd, staging=staging)
        if process.returncode != 0:
            errors.append("{0} stdout: {1!r} stderr: {2!r}".format(cmd, stdout,
                                                                   stderr))

    # Untag builds first due to koji/mash bug:
    # https://fedorahosted.org/koji/ticket/299
    # FIXME: This introduces a theoretical race condition when a package is
    # built after all builds were untagged and before the package is blocked
    cmd = ["untag-build", "--all", tag] + packages
    catch_koji_errors(cmd)

    cmd = ["block-pkg", tag] + packages
    catch_koji_errors(cmd)

    #If a package moves from EPEL to RHEL it can only be built if it is unblocked
    #in the epel build tag. Therefore unblock all retired EPEL packages in the
    #built tag since it does not hurt if the package does not move to RHEL.
    if epel_build_tag:
        cmd = ["unblock-pkg", epel_build_tag] + packages
        catch_koji_errors(cmd)

    return errors


def block_all_retired(branches=RETIRING_BRANCHES, staging=False,
                      namespace=DEFAULT_NS):
    for branch in branches:
        log.debug("Processing branch %s", branch)
        if staging and branch in PROD_ONLY_BRANCHES:
            log.warning('%s in namespace "%s" not handled in staging..' %
                        (branch, namespace))
            continue
        retired = get_retired_packages(branch, staging, namespace)
        unblocked = []

        # Check which packages are included in a tag but not blocked, this
        # ensures that no packages not included in a tag are tried to be
        # blocked. Packages might not be in the rawhide tag if they are retired
        # too fast, e.g. because they are EPEL-only
        allunblocked = unblocked_packages(branch, staging, namespace)
        for pkg in retired:
            if pkg in allunblocked:
                unblocked.append(pkg)

        errors = block_package(unblocked, branch, staging=staging, namespace=namespace)
        # Block packages individually so that errors with one package does not
        # stop the other packages to be blocked
        if errors:
            for error in errors:
                log.error(error)
            for package in unblocked:
                errors = block_package(package, branch, staging=staging, namespace=namespace)
                log.info("Blocked %s on %s in namespace %s", package, branch, namespace)
                for error in errors:
                    log.error(error)


def setup_logging(debug=False, mail=False):
    if debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s: %(levelname)s: %(message)s',
    )
    # Log in UTC
    formatter.converter = time.gmtime

    console_logger = logging.StreamHandler()
    if debug:
        console_logger.setLevel(logging.DEBUG)
    else:
        console_logger.setLevel(logging.INFO)
    console_logger.setFormatter(formatter)
    log.addHandler(console_logger)

    if mail:
        # FIXME: Make this a config option
        fedora_user = getpass.getuser()
        mail_logger = SubjectSMTPHandler(
            "127.0.0.1", fedora_user, [fedora_user], "block_retired event")
        if debug:
            mail_logger.setLevel(logging.DEBUG)
        mail_logger.setFormatter(formatter)
        mail_logger.subject_prefix = "Package Blocker: "
        log.addHandler(mail_logger)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Block retired packages")
    parser.add_argument("--debug", default=False, action="store_true")
    parser.add_argument("packages", nargs="*", metavar="package",
                        help="Packages to block, default all retired packages")
    parser.add_argument(
        "--branch", default="rawhide",
        help="Branch to retire specified packages on, default: %(default)s")
    parser.add_argument(
        "--staging", default=False, action="store_true",
        help="Talk to staging services (pdc), instead of production")
    parser.add_argument(
        "-p", "--profile", default="koji",
        help="Koji profile to use, default: %(default)s (ignored with --staging)")
    parser.add_argument(
        "--namespace", default=DEFAULT_NS,
        help="pdc namespace to use, default: %(default)s")
    args = parser.parse_args()

    setup_logging(args.debug)

    PRODUCTION_KOJI_PROFILE = args.profile
    STAGING_KOJI_PROFILE = "stg"
    if not args.packages:
        block_all_retired(staging=args.staging, namespace=args.namespace)
    else:
        block_package(args.packages, args.branch, staging=args.staging,
                      namespace=args.namespace)
