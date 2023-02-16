#!/bin/python3

# a python script that collects all the packages in 
# https://src.fedoraproject.org/rpms,
# checks if they are retired and queries pdc to confirm 
# they are not listed as active there.


import json
import requests

token = ""
dist_git_base = "https://src.fedoraproject.org"


session = requests.Session()

# 1. Collect /rpms packages

def retrieve_names():
    rpms_projects = []
    url = f"{dist_git_base}/api/0/projects?namespace=rpms&fork=False&per_page=50"
    while url:
        req = session.get(url)
        data = req.json()
        for project in data.get("projects", []):
            project_name = project["name"]
            if project_name not in rpms_projects:
                rpms_projects.append(project_name)
        url = data.get("pagination", {}).get("next")
        print(f"Going to the next url: {url}")
        if not url:
            print("Finished!")
            break

    print(rpms_projects)
    with open('project_names.txt', 'w') as f:
        json.dump(rpms_projects, f, ensure_ascii=False)

# 2. Select the retired ones

def check_if_retired():
    dead_packages = []
    with open('project_names.txt') as f:
        data = json.load(f)
    for project in data:
        print(project)
        url = f"{dist_git_base}/rpms/{project}/raw/rawhide/f/dead.package"
        print(url)
        if is_dead(url):
            dead_packages.append(project)
            print(f"This project is dead: {project}, {dead_packages}")
    with open("dead_packages.txt", "w") as f:
        json.dump(dead_packages, f, ensure_ascii=False)


def is_dead(url):
    """
    This will simply check if the string 'dead.package' appears anywhere
    in the files section of this package
    """
    response = requests.get(url)
    if response.ok:
        return True
    else:
        return False


def check_if_active_in_pdc():
    """
    This function loads the dead packages and checks if they are active in pdc
    """
    with open('dead_packages.txt') as f:
        packages = json.load(f)
    dead_and_active = []
    for package in packages:
        print(package)
        try:
            url = f"https://pdc.fedoraproject.org/rest_api/v1/component-branches/?global_component={package}&type=rpm&active=true"
            req = session.get(url)
            data = req.json()
            if data.get("count") != 0:
                dead_and_active.append(package)
                print(f"This project is dead and acive in pdc: {package}")
            print(dead_and_active)
        except requests.exceptions.ConnectionError:
            print("Reconnecting")
            continue
        with open("dead_and_active.txt", "w") as f:
            json.dump(dead_and_active, f, ensure_ascii=False)


def refine_results_regarding_branches():
    """
    This function loads the packages that are dead in distgit and active in pdc
    and checks branch by branch that the dead ones in distgit are dead in pdc as well.
    In case there is a package with retired branch which appears active in pdc, 
    it outputs to a file.
    """
    refined_dead_and_active = []
    with open("dead_and_active.txt") as f:
        refined_packages = json.load(f)
        for package in refined_packages:
            branches = []
            try:
                url = f"https://pdc.stg.fedoraproject.org/rest_api/v1/component-branches/?global_component={package}&type=rpm&active=true"
                req = session.get(url)
                data = req.json()
                number_branches = len(data.get("results"))
                print(f"package: {package}, number of active branches: {number_branches}")
            except requests.exceptions.ConnectionError:
                print("Reconnecting")
                continue
 
            for number in range(number_branches):
                branch = data.get("results")[number].get("name")
                print(f"branch name: {branch}")
                branches.append(branch)
            for active_branch in branches:
                print(f"branches: {branches}")
                try:
                    # Check if dead in distgit
                    distgit_url = f"https://src.fedoraproject.org/rpms/copr-builder/raw/{branch}/f/dead.package"
                    if is_dead(distgit_url):
                        print(f"Package: {package}, active_branch name: {active_branch}, url: {distgit_url}, is dead")
                        pdc_url = f"https://pdc.stg.fedoraproject.org/rest_api/v1/component-branches/?global_component=copr-builder&type=rpm&active=true&name={active_branch}"
                        request = session.get(pdc_url)
                        data_dead = request.json()
                except requests.exceptions.ConnectionError:
                    print("Reconnecting")
                    continue

                    if data_dead.get("count") != 0:
                        refined_dead_and_active.append(f"Package: {package}, {active_branch}")
                        print("BEHOLD!!!!!!!!!!!!")
                        print(f"Package: {package}, active_branch name: {active_branch}, url: {url}, is active in pdc!")
                        with open("dead_including_branches.txt", "w") as f:
                            json.dump(refined_dead_and_active, f, ensure_ascii=False)


if __name__ == "__main__":
    try:
        #retrieve_names()
        #check_if_retired()
        #check_if_active_in_pdc()
        refine_results_regarding_branches()
    except KeyboardInterrupt:
        pass
