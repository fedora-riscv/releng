#!/usr/bin/env python3
"""
    This script will find and list the contributors of a fedora src package using json,
    Then list the slas from the pdc.fedoraproject.org of the specified package.
    Lastly it will check if the package contains the dead.package file.
    Methods are currently called by default and output will stdout.

    Authors:
        Ariel Lima <alima@redhat.com> -- Red Hat Intern 2018 Summer
"""

import requests
import argparse
import sys
import datetime as dt

"""
    Parsing:

    nms: This is the namespace, not necessary default is "rpms"
    pck: This is the name of the fedora package, user has to input this, has no default value
    brc: This is the specific branch, not necessary default is "rawhide"
"""
parser = argparse.ArgumentParser()
parser.add_argument("--nms", help="Name of the namespace that contains package", type=str, default="rpms")
parser.add_argument("pck", help="Name of the fedora package", type=str)
parser.add_argument("--brc", help="Name of the branched version of the package wanted", type=str, default="rawhide")
args = parser.parse_args()

# this is the default url used for getting contributors the url is api/0/<namespace>/<package>
contributors_url = f"https://src.fedoraproject.org/api/0/{args.nms}/{args.pck}"

# this is the default url that we will use get the slas
slas_url = f"https://pdc.fedoraproject.org/rest_api/v1/component-branches/?global_component={args.pck}&name={args.brc}&type={args.nms[:-1]}"

# this url will be the default url used to check if a package is a dead package or not
state_url = f"https://src.fedoraproject.org/{args.nms}/{args.pck}/raw/{args.brc}/f/dead.package"


def package_contributors(url):
    """
        This is a very simple method that will return the contributors of the package specified
    """
    try:
        # This is really just to make sure that we got to the url we want
        # quit if there is any error
        response = requests.get(url)
        if not response.ok:
            sys.exit(0)
        response = response.json()
    except Exception:
        print("ERROR: not able to find main page [package contributor method], could be due to wrong input or code update may be needed")

    owner = response['access_users']['owner']
    admins = response['access_users']['admin']
    contributors = owner + admins

    # we check to see whether it is an orphan package or not
    # then this is just basic outputting into a format I think looks good
    if(owner[0] == "orphan"):
        print("\n*THIS IS AN ORPHAN PACKAGE*")
    else:
        print("\nOWNER:\n-" + (contributors[0]))

    # we check for admins, we could have this implemented into the previous if statement, I didn't because I am not fully aware of the standards for packages
    # we check for any admins, then format it in, case there is one
    if(len(admins) >= 1):
        print("\nADMINS: ")
        for p in admins:
            print("-"+str(p))

    return contributors


def package_slas(url):
    """
        this returns the slas of a package
    """
    try:
        # This is really just to make sure that we got to the url we want
        # quit if there is any error
        response = requests.get(url)
        if not response.ok:
            sys.exit(0)
        response = response.json()
    except Exception:
        print("ERROR: not able to find SLA page [package_slas method], could be due to wrong input or code update may be needed")

    response = response['results'][0]['slas']
    print("\nSLAS--")
    for item in response[0]:
        print(str(item) + ":" + str(response[0][item]))
        if str(item) == "eol":
            eol = dt.datetime.strptime(str(response[0][item]), "%Y-%m-%d")
            delta = dt.datetime.utcnow() - eol
            if delta > dt.timedelta(days=56):
                print("Package was retired more than 8 weeks ago. Need a new review")
            else:
                print("Package does not need a new review.")
    print("\n")


def package_state(url):
    """
        This will simply check if the string 'dead.package' appears anywhere in the files section of this package
    """
    response = requests.get(url)
    if response.ok:
        print("This package has a dead.package file\n")
    else:
        print("No dead.package file\n")


if __name__ == '__main__':
    package_contributors(contributors_url)
    package_slas(slas_url)
    package_state(state_url)
