#!/usr/bin/python3
#
# mass_rebuild_file_bugs.py - A utility to discover failed builds in a
#    given tag and file bugs in bugzilla for these failed builds
#
# Copyright (C) 2013 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0+
#
# Authors:
#     Stanislav Ochotnicky <sochotnicky@redhat.com>
#

from __future__ import print_function
import koji
import getpass
import tempfile
import urllib
from bugzilla.rhbugzilla import RHBugzilla
from xmlrpc.client import Fault
from find_failures import get_failed_builds

# contains info about all rebuilds, add new rebuilds there and update rebuildid
# here
from massrebuildsinfo import MASSREBUILDS

rebuildid = 'f34'
failures = {} # dict of owners to lists of packages that failed.
failed = [] # raw list of failed packages

bzurl = 'https://bugzilla.redhat.com'
BZCLIENT = RHBugzilla(url="%s/xmlrpc.cgi" % bzurl,
                      user="releng@fedoraproject.org")

DEFAULT_COMMENT = \
"""{component} failed to build from source in {product} {version}/f{rawhide_version}

https://koji.fedoraproject.org/koji/taskinfo?taskID={task_id}
{extrainfo}

For details on the mass rebuild see:

{wikipage}
Please fix {component} at your earliest convenience and set the bug's status to
ASSIGNED when you start fixing it. If the bug remains in NEW state for 8 weeks,
{component} will be orphaned. Before branching of {product} {nextversion},
{component} will be retired, if it still fails to build.

For more details on the FTBFS policy, please visit:
https://docs.fedoraproject.org/en-US/fesco/Fails_to_build_from_source_Fails_to_install/
"""

def report_failure(massrebuild, component, task_id, logs,
                   summary="{component}: FTBFS in {product} {version}/f{rawhide_version}",
                   comment=DEFAULT_COMMENT, extrainfo=""):
    """This function files a new bugzilla bug for component with given
    arguments

    Keyword arguments:
    massrebuild -- generic info about mass rebuild such as tracking_bug,
    Bugzilla product, version, wikipage
    component -- component (package) to file bug against
    task_id -- task_id of failed build
    logs -- list of URLs to the log file to attach to the bug report
    summary -- short bug summary (if not default)
    comment -- first comment describing the bug in more detail (if not default)
    """

    format_values = dict(**massrebuild)
    format_values["task_id"] = task_id
    format_values["component"] = component
    format_values["nextversion"] = str(int(massrebuild["rawhide_version"]) + 1)
    format_values["extrainfo"] = extrainfo

    summary = summary.format(**format_values)
    comment = comment.format(**format_values)

    data = {'product': massrebuild["product"],
            'component': component,
            'version': massrebuild["version"],
            'short_desc': summary,
            'comment': comment,
            'blocks': massrebuild["tracking_bug"],
            'rep_platform': 'Unspecified',
            'bug_severity': 'unspecified',
            'op_sys': 'Unspecified',
            'bug_file_loc': '',
            'priority': 'unspecified',
           }


    try:
        print('Creating the bug report')
        bug = BZCLIENT.createbug(**data)
        bug.refresh()
        print(bug)
        attach_logs(bug, logs)
    except Fault as ex:
        print(ex)
        #Because of having image build requirement of having the image name in koji
        #as a package name, they are missing in the components of koji and we need
        #to skip them.
        #if ex.faultCode == -32000:
        #    print(component)
        if "There is no component" in ex.faultString:
            print(ex.faultString)
            return None
        else:
            username = input('Bugzilla username: ')
            BZCLIENT.login(user=username,
                           password=getpass.getpass())
            return report_failure(massrebuild, component, task_id, logs, summary,
                                  comment)
    return bug

def attach_logs(bug, logs):

    if isinstance(bug, int):
        bug = BZCLIENT.getbug(bug)

    for log in logs:
        name = log.rsplit('/', 1)[-1]
        try:
            response = urllib.request.urlopen(log)
        except urllib.error.HTTPError as e:
            #sometimes there wont be any logs attached to the task.
            #skip attaching logs for those tasks
            if e.code == 404:
                print("Failed to attach {} log".format(name))
                continue
            else:
                break
        fp = tempfile.TemporaryFile()

        CHUNK = 2 ** 20
        while True:
            chunk = response.read(CHUNK)
            if not chunk:
                break
            fp.write(chunk)

        filesize = fp.tell()
        # Bugzilla file limit, still possibly too much
        # FILELIMIT = 32 * 1024
        # Just use 32 KiB:
        FILELIMIT = 2 ** 15
        if filesize > FILELIMIT:
            fp.seek(filesize - FILELIMIT)
            comment = "file {} too big, will only attach last {} bytes".format(
                name, FILELIMIT)
        else:
            comment = ""
            fp.seek(0)
        try:
            print('Attaching file %s to the ticket' % name)
            # arguments are: idlist, attachfile, description, ...
            attid = BZCLIENT.attachfile(
                bug.id, fp, name, content_type='text/plain', file_name=name,
                comment=comment
            )
        except Fault as  ex:
            print(ex)
            raise

        finally:
            fp.close()

def get_filed_bugs(tracking_bug):
    """Query bugzilla if given bug has already been filed

    arguments:
    tracking_bug -- bug used to track failures
    Keyword arguments:
    product -- bugzilla product (usually Fedora)
    component -- component (package) to file bug against
    version -- component version to file bug for (usually rawhide for Fedora)
    summary -- short bug summary
    """
    query_data = {'blocks': tracking_bug}
    bzurl = 'https://bugzilla.redhat.com'
    bzclient = RHBugzilla(url="%s/xmlrpc.cgi" % bzurl)

    return bzclient.query(query_data)

def get_task_failed(kojisession, task_id):
    ''' For a given task_id, use the provided kojisession to return the
    task_id of the first children that failed to build.
    '''
    for child in kojisession.getTaskChildren(task_id):
        if child['state'] == koji.TASK_STATES["FAILED"]:  # 5 == Failed
            return child['id']


if __name__ == '__main__':
    massrebuild = MASSREBUILDS[rebuildid]

    kojisession = koji.ClientSession('https://koji.fedoraproject.org/kojihub')
    print('Getting the list of failed builds...')
    failbuilds = get_failed_builds(kojisession, massrebuild['epoch'],
                                   massrebuild['buildtag'],
                                   massrebuild['desttag'])
    print('Getting the list of filed bugs...')
    filed_bugs = get_filed_bugs(massrebuild['tracking_bug'])
    filed_bugs_components = [bug.component for bug in filed_bugs]
    for build in failbuilds:
        task_id = build['task_id']
        component = build['package_name']
        work_url = 'https://kojipkgs.fedoraproject.org/work'

        child_id = get_task_failed(kojisession, task_id)
        if not child_id:
            print('No children failed for task: %s (%s)' % (
                task_id, component))
            logs = []
        else:
            base_path = koji.pathinfo.taskrelpath(child_id)
            log_url = "%s/%s/" % (work_url, base_path)
            build_log = log_url + "build.log"
            root_log = log_url + "root.log"
            state_log = log_url + "state.log"
            logs = [build_log, root_log, state_log]


        if component not in filed_bugs_components:
            print("Filing bug for %s" % component)
            report_failure(massrebuild, component, task_id, logs)
            filed_bugs_components.append(component)
        else:
            print("Skipping %s, bug already filed" % component)
