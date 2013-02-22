#!/usr/bin/python
#
# mass_rebuild_file_bugs.py - A utility to discover failed builds in a given tag
#                    and file bugs in bugzilla for these failed builds
#
# Copyright (c) 2009 Red Hat
#
# Authors:
#     Stanislav Ochotnicky <sochotnicky@redhat.com>
#

import koji
import getpass
from bugzilla.rhbugzilla import RHBugzilla
from xmlrpclib import Fault
from find_failures import get_failed_builds

# Set some variables
# Some of these could arguably be passed in as args.
buildtag = 'f18-rebuild' # tag to check
desttag = 'f18' # Tag where fixed builds go
epoch = '2012-07-17 14:18:03.000000' # Date to check for failures from
failures = {} # dict of owners to lists of packages that failed.
failed = [] # raw list of failed packages

product = "Fedora" # for BZ product field
version = "rawhide" # for BZ version field

def report_failure(product, component, version, summary, comment):
    """This function files a new bugzilla bug for component with given arguments

    Keyword arguments:
    product -- bugzilla product (usually Fedora)
    component -- component (package) to file bug against
    version -- component version to file bug for (usually rawhide for Fedora)
    summary -- short bug summary
    comment -- first comment describing the bug in more detail"""
    data = {
        'product': product,
        'component': component,
        'version': version,
        'short_desc': summary,
        'comment': comment,
        'rep_platform': 'Unspecified',
        'bug_severity': 'unspecified',
        'op_sys': 'Unspecified',
        'bug_file_loc': '',
        'priority': 'unspecified',
        }
    bzurl = 'https://bugzilla.redhat.com'
    bzclient = RHBugzilla(url="%s/xmlrpc.cgi" % bzurl)
    try:
        bug = bzclient.createbug(**data)
        print "Running bzcreate: %s" % data
        bug.refresh()
    except Fault, ex:
        print ex
        username = raw_input('Bugzilla username: ')
        bzclient.login(user=username,
                       password=getpass.getpass())
        report_failure(component, summary, comment)

if __name__ == '__main__':
    kojisession = koji.ClientSession('http://koji.fedoraproject.org/kojihub')
    failbuilds = get_failed_builds(kojisession, epoch, buildtag, desttag)

    for build in failbuilds:
        task_id = build['task_id']
        component = build['package_name']
        summary = "FTBFS: %s in %s" % (component, 'rawhide')
        work_url = 'http://kojipkgs.fedoraproject.org/work'
        base_path = koji.pathinfo.taskrelpath(task_id)
        log_url = "%s/%s/" % (work_url, base_path)
        build_log = log_url + "build.log"
        root_log = log_url + "root.log"
        state_log = log_url + "state.log"
        comment = """Your package %s failed to build from source in current rawhide.

Build logs:
root.log: %s
build.log: %s
state.log: %s


""" % (component, root_log, build_log, state_log)

        report_failure(product, component, version, summary, comment)
