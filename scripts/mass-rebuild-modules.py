#!/usr/bin/python3

"""
Author: Mohan Boddu <mboddu@bhujji.com>
"""

from __future__ import print_function
from pprint import pprint
import os
import subprocess
import sys
import operator
import requests
import json
import argparse
import time

import gi
gi.require_version('Modulemd', '2.0')
from gi.repository import Modulemd

from massrebuildsinfo import MASSREBUILDS

rebuildid = 'f31'
massrebuild = MASSREBUILDS[rebuildid]
user = 'Fedora Release Engineering <releng@fedoraproject.org>'
comment = '- Rebuilt for ' + massrebuild['wikipage']
module_mass_rebuild_epoch = massrebuild['module_mass_rebuild_epoch']
module_mass_branching_epoch = massrebuild['module_mass_branching_epoch']
workdir = os.path.expanduser('~/mass_branch_modules')
enviro = os.environ


# Define functions

# This function needs a dry-run like option
def runme(cmd, action, pkg, env, cwd=workdir):
    """Simple function to run a command and return 0 for success, 1 for
       failure.  cmd is a list of the command and arguments, action is a
       name for the action (for logging), pkg is the name of the package
       being operated on, env is the environment dict, and cwd is where
       the script should be executed from."""

    try:
        subprocess.check_call(cmd, env=env, cwd=cwd)
    except subprocess.CalledProcessError as e:
        sys.stderr.write('%s failed %s: %s\n' % (pkg, action, e))
        return 1
    return 0

# This function needs a dry-run like option
def runmeoutput(cmd, action, pkg, env, cwd=workdir):
    """Simple function to run a command and return output if successful.
       cmd is a list of the command and arguments, action is a
       name for the action (for logging), pkg is the name of the package
       being operated on, env is the environment dict, and cwd is where
       the script should be executed from.  Returns 0 for failure"""

    try:
        pid = subprocess.Popen(cmd, env=env, cwd=cwd,
                               stdout=subprocess.PIPE, encoding='utf8')
    except BaseException as e:
        sys.stderr.write('%s failed %s: %s\n' % (pkg, action, e))
        return 0
    result = pid.communicate()[0].rstrip('\n')
    return result

parser = argparse.ArgumentParser()
parser.add_argument('token_file', help='MBS token file for authentication.')
#During mass rebuild, we need to check if a module has build time dependencies on module_mass_rebuild_platform
#During mass branching, we need to check if a module has run time dependencies on module_mass_branching_platform
parser.add_argument('process', help='build or branch, build is used during mass rebuild time, branch is used during branching time')
parser.add_argument(
    '--wait',
    action='store_true',
    help='Wait until each module build completes/fails before moving on to the next',
)
args = parser.parse_args()

if __name__ == '__main__':
    token_file = args.token_file
    process = args.process
    wait = args.wait
    with open(token_file, 'r', encoding='utf-8') as f:
        token = f.read().strip()
    pdc = 'https://pdc.fedoraproject.org/'
    modules = []
    #Query pdc to get the modules that are not eol'd
    url = '{0}/rest_api/v1/component-branch-slas/?page_size=100&branch_type=module&branch_active=1'.format(pdc)
    while True:
        rv = requests.get(url)
        if not rv.ok:
            raise RuntimeError('Failed with: {0}'.format(rv.text))
        rv_json = rv.json()
        for sla in rv_json['results']:
            module = {}
            #module['module_name'] = sla['branch']['global_component']
            #module['module_stream'] = sla['branch']['name']
            module[sla['branch']['global_component']] = sla['branch']['name']
            if not module in modules:
                modules.append(module)
        url = rv_json['next']
        if not url:
            break
    #print(modules)

    # Environment for using releng credentials for pushing and building
    enviro['GIT_SSH'] = '/usr/local/bin/relengpush'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(token)
    }

    for module in modules:
        if(len(list(module.keys()))) > 1:
            print('Something is wrong, {} has more than 1 stream in the dict'.format(list(module.keys())[0]))
            continue
        else:
            name = list(module.keys())[0]
            stream = module[name]
            #Get the list of builds that are submitted after the module epoch datetime
            #Use this info to figure out whether you need to resubmit the build or not
            #This is useful when the script execution fails for unknown reasons and
            #dont have to submit all the builds again.
            if process == 'build':
                mbs="https://mbs.fedoraproject.org/module-build-service/1/module-builds/?submitted_after={}&name={}&stream={}&state=ready&state=init&state=wait&state=build&state=done".format(module_mass_rebuild_epoch,name,stream)
            elif process == 'branch':
                mbs="https://mbs.fedoraproject.org/module-build-service/1/module-builds/?submitted_after={}&name={}&stream={}&state=ready&state=init&state=wait&state=build&state=done".format(module_mass_branching_epoch,name,stream)
            else:
                print("Please select either build or branch for the process type")
                sys.exit(1)

            rv = requests.get(mbs)
            if not rv.ok:
                print("Unable to get info about {} module and {} stream, skipping the build".format(name,stream))
                continue
            rv_json = rv.json()
            #Check if a module build is already submitted after the epoch date
            if rv_json['meta']['total'] != 0:
                print("Skipping {} module build for {} stream, since its already built".format(name,stream))
            else:
                # Check if the clone already exists
                if not os.path.exists(os.path.join(workdir, name)):
                    # Clone module git
                    fedpkgcmd = ['fedpkg', '--user', 'releng', 'clone', 'modules/'+name]
                    print('Cloning module %s' % name)
                    if runme(fedpkgcmd, 'fedpkg', name, enviro):
                        continue

                # Checkout the stream branch
                fedpkgcheckoutcmd = ['fedpkg', 'switch-branch', stream]
                print('Checking out the %s stream branch' % stream)
                if runme(fedpkgcheckoutcmd, 'fedpkg', stream, enviro,
                                 cwd=os.path.join(workdir, name)):
                    continue

                # Check for a noautobuild file
                if os.path.exists(os.path.join(workdir, name, 'noautobuild')):
                    # Maintainer does not want us to auto build.
                    print('Skipping %s due to opt-out' % name)
                    continue

                # Find the modulemd file
                if os.path.exists(os.path.join(workdir, name, name+'.yaml')):
                    modulemd = os.path.join(workdir, name, name+'.yaml')
                else:
                    sys.stderr.write('%s failed modulemd check\n' % name)
                    continue

                #Use libmodulemd to determine if this module stream applies to this platform version
                try:
                    mmd = Modulemd.ModuleStream.read_file(modulemd, True)
                except:
                    print("Could not able to read the modulemd file")
                    continue
                if process == 'build':
                    platform = massrebuild['module_mass_rebuild_platform']
                    #check if a module has build time dependency on platform
                    needs_building = mmd.build_depends_on_stream('platform', platform)
                elif process == 'branch':
                    platform = massrebuild['module_mass_branching_platform']
                    #check if a module has run time dependency on platform
                    needs_building = mmd.depends_on_stream('platform', platform)
                else:
                    print("Please select either build or branch for the process type")
                    sys.exit(1)


                if not needs_building:
                    print("Not required to build module {} for stream {}".format(name,stream))
                    continue
                else:
                    # Set the git user.name and user.email
                    set_name = ['git', 'config', 'user.name', 'Fedora Release Engineering']
                    set_mail = ['git', 'config', 'user.email', 'releng@fedoraproject.org']
                    print('Setting git user.name and user.email')
                    if runme(set_name, 'set_name', name, enviro,
                                 cwd=os.path.join(workdir, name)):
                        continue
                    if runme(set_mail, 'set_mail', name, enviro,
                                 cwd=os.path.join(workdir, name)):
                        continue

                    # Empty git commit
                    if process == 'build':
                        commit = ['git', 'commit', '-s', '--allow-empty', '-m', comment]
                    elif process == 'branch':
                        commit = ['git', 'commit', '-s', '--allow-empty', '-m', 'Branching {} from rawhide, second attempt after platform:f31 enablement'.format(rebuildid)]
                    else:
                        print("Please select either build or branch for the process type")
                        sys.exit(1)
                    print('Committing changes for %s' % name)
                    if runme(commit, 'commit', name, enviro,
                                 cwd=os.path.join(workdir, name)):
                        continue

                    #Push the empty commit
                    push = ['fedpkg', 'push']
                    print('Pushing changes for %s' % name)
                    if runme(push, 'push', name, enviro,
                                 cwd=os.path.join(workdir, name)):
                        continue

                    # get git url
                    urlcmd = ['fedpkg', 'giturl']
                    print('Getting git url for %s' % name)
                    url = runmeoutput(urlcmd, 'giturl', name, enviro,
                                 cwd=os.path.join(workdir, name))
                    if not url:
                        continue
                    #mbs requires git url to have ?# before git hash
                    #whereas fedpkg giturl returns just # before the hash
                    #This will replace # with ?# for this reason
                    url = url.replace('#', '?#')

                    # Module build
                    # For mass rebuild we need to rebuild all modules again
                    # For mass branching, since we can reuse already existing
                    # modules, we dont need rebuild_strategy = all option.
                    # This saves time and resources
                    if process == 'build':
                        data = json.dumps({
                            'scmurl': url,
                            'branch': stream,
                            'rebuild_strategy': 'all'
                        })
                    elif process == 'branch':
                        data = json.dumps({
                            'scmurl': url,
                            'branch': stream,
                        })
                    else:
                        print("Please select either build or branch for the process type")
                        sys.exit(1)

                    rv = requests.post('https://mbs.fedoraproject.org/module-build-service/2/module-builds/', data=data, headers=headers)
                    if rv.ok:
                        print('Building {} module for stream {}'.format(name,stream))
                        #pprint(rv.json())
                        if not wait:
                            continue

                        build_id = rv.json()['id']
                        build_url = (
                            'https://mbs.fedoraproject.org/module-build-service/2/module-builds/{}?short=true'
                            .format(build_id)
                        )
                        while True:
                            print('Waiting for 15 seconds')
                            time.sleep(15)
                            print('Checking the status of module build {}'.format(build_id))
                            get_rv = requests.get(build_url, timeout=15)
                            # If the get request fails, simply try again in 15 seconds
                            if not get_rv.ok:
                                continue

                            state = get_rv.json()['state_name']
                            if state in ('failed', 'ready'):
                                print('The module build {} completed and is in the {} state'.format(build_id, state))
                                break
                    elif rv.status_code == 401:
                        print('The token is unauthorized', file=sys.stderr)
                        print(rv.text)
                        sys.exit(1)
                    else:
                        print(rv.text)
                        print('Unable to submit the module build {} for branch {}'.format(name,stream))
