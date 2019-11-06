#!/usr/bin/env python3
"""
    This script will find and list the contributors of a fedora src package using json,
    Then list the slas from the pdc.fedoraproject.org of the specified package.
    Lastly it will check if the package contains the dead.package file.
    Methods are currently called by default and output will stdout.

    Authors:
        Ariel Lima <alima@redhat.com> -- Red Hat Intern 2018 Summer
"""

import requests#used to make requests to urls
import argparse#we want to be able to take different inputs to format different urls
import sys#only used to succesfully terminate script in case of error
import re#we use this so we can easily manipulate the url
import json#What we pull from the url will be in json format

from bs4 import BeautifulSoup#we will use beautiful soup to go though an html page in search of dead.package files
"""
    Parsing:

    nms: This is the namespace, not necessary default is "rpms"
    pck: This is the name of the fedora package, user has to input this, has no default value
    brc: This is the specific branch, not necessary default is "master"
"""
parser = argparse.ArgumentParser()
parser.add_argument("--nms", help="Name of the namespace that contains package", type=str)#namespace package is located in
parser.add_argument("pck", help="Name of the fedora package",type=str)#package name
parser.add_argument("--brc", help="Name of the branched version of the package wanted", type=str)#name of the branched version of package wanted
args = parser.parse_args()

#this is the default url used for getting contributors the url is api/0/<namespace>/<package>
contributors_url = ("https://src.fedoraproject.org/api/0/rpms/"+args.pck)

#this is the default url that we will use get the slas
slas_url = "https://pdc.fedoraproject.org/rest_api/v1/component-branches/?global_component="+args.pck+"&name=master&type=rpm"

#this url will be the default url used to check if a package is a dead package or not
state_url = "https://src.fedoraproject.org/rpms/"+args.pck+"/tree/master"

"""
    This is where the argument parsing will happen
"""
if args.nms:
    #case nms argument is used we want to modify the default namespace
    if 'rpm' not in args.nms:
        contributors_url = re.sub("/rpms/", ("/"+args.nms+"/"), contributors_url)#I added the forward slashes as a means to attempt to minimalize errors
        slas_url = re.sub("type=rpm", ("type="+args.nms), slas_url)#Includes 'type' as precaution to possible packagename issues
        state_url = re.sub("/rpms/", ("/"+args.nms+"/"), state_url)#When a user specifies a namespace that is not defult we change it
        print(contributors_url, slas_url)
if args.brc:
    #case we want to change the branch we get the slas from (default is master)
    slas_url = re.sub("name=master", ("name="+args.brc), slas_url)#Includes 'name' as precaution to possible packagename issues
    state_url = re.sub("tree/master", ("tree/"+args.brc), state_url)#when a user specifies a branch that is not default we change it in the url

def package_contributors(url):
    """
        This is a very simple method that will return the contributors of the package specified
    """
    try:
        #This is really just to make sure that we got to the url we want
        #quit if there is any error
        response = requests.get(url)#here we have the extra step to ensure that we did not get an error (not converting straight to json)
        if(str(response)!="<Response [200]>"):
            sys.exit(0)
        response = response.json()
    except:
        print("ERROR: not able to find main page [package contributor method], could be due to wrong input or code update may be needed")

    owner = response['access_users']['owner']#Current owner of this package (main_admin)
    admins = response['access_users']['admin']#current admins of this package in list format
    contributors = owner + admins#owner located at index 0, rest are admins

    #we check to see whether it is an orphan package or not
    #then this is just basic outputting into a format I think looks good
    if(owner[0]=="orphan"):
        print("\n*THIS IS AN ORPHAN PACKAGE*")
    else:
        print("\nOWNER:\n-" + (contributors[0]))

    #we check for admins, we could have this implemented into the previous if statement, I didn't because I am not fully aware of the standards for packages
    #we check for any admins, then format it in, case there is one
    if(len(admins)>=1):
        print("\nADMINS: ")
        for p in admins:
            print("-"+str(p))

    return contributors#in case someone needs this for something else in the future we return the list of contributers, index 0 is owner

def package_slas(url):
    """
        this returns the slas of a package
    """
    try:
        #This is really just to make sure that we got to the url we want
        #quit if there is any error
        response = requests.get(url)#***here we have the extra step to ensure that we did not get an error (not converting straight to json)
        if(str(response)!="<Response [200]>"):
            sys.exit(0)
        response = response.json()#***here we finally convert it to json
    except:
        print("ERROR: not able to find SLA page [package_slas method], could be due to wrong input or code update may be needed")

    response=response['results'][0]['slas']#here we specify very clearly what we want from the json object, response now becomes a list of dictionaries
    #From here down is just basic outputting into a format I think looks good
    print("\nSLAS--")
    for item in response[0]:
        print(str(item) + ":" + str(response[0][item]))
    print("\n")

def package_state(url):
    """
        This will simply check if the string 'dead.package' appears anywhere in the files section of this package
    """
    try:
        #This is really just to make sure that we got to the url we want
        #quit if there is any error
        response = requests.get(url)
        if(str(response)!="<Response [200]>"):
            sys.exit(0)
        soup = BeautifulSoup(response.content, 'html.parser')#create a beautiful soup object, pretty much all I know
    except:
        print("ERROR: not able to find file url[package_state method], could be due to wrong input or code update may be needed")

    soup = str(soup)#we will turn soup into a string object to facilitate searching for a sequence

    if("dead.package" in soup):#search for dead.package sequence
        print("This package has a dead.package file\n")
    else:
        print("No dead.package file\n")
package_contributors(contributors_url)#function call
package_slas(slas_url)#function call
package_state(state_url)#function call
