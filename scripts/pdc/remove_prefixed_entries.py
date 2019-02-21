"""
This script will get list of all entries for selected fedora release,
from pdc https://pdc.fedoraproject.org/rest_api/v1/component-branches/?active=true&type=rpm&name=f30
And for each item in that list, check if the name (global_component) starts with prefix and delete it.
"""
import requests
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('token', help='PDC token for authentication.')
parser.add_argument('branch', help='Name of the branch (f30)')
parser.add_argument('prefix', help='Package prefix like rust-, or nodejs-')
parser.add_argument('dryrun', help='Do not delete anything just use print', nargs='?', const=True, default=True)

args = parser.parse_args()

if __name__ == '__main__':
    token = args.token
    prefix = args.prefix
    branch = args.branch
    dry = args.dryrun
    pdc = 'https://pdc.fedoraproject.org/'
    url = '{0}/rest_api/v1/component-branches/?' \
          '&fields=name&fields=id&fields=global_component' \
          '&active=true&type=rpm&name={1}'.format(pdc, branch)
    headers = {'Content-Type': 'application/json', 'Authorization': 'token {0}'.format(token)}
    packages = []
    while True:
        rv = requests.get(url)
        if not rv.ok:
            raise RuntimeError('Failed with: {0}'.format(rv.text))
        rv_json = rv.json()
        for component in rv_json['results']:
            if component['global_component'].startswith(prefix):
                if dry:
                    print("========== Dry Run ==========")
                    print(component['global_component'])
                    print(component['id'])
                    print("=============================")
                else:
                    delete_url = '{0}/rest_api/v1/component-branches/{1}'.format(pdc, component['id'])
                    rv = requests.delete(delete_url, headers=headers)
                    if not rv.ok:
                        raise RuntimeError('Failed with: {0}'.format(rv.text))
                packages.append({"name": component['global_component'],
                                 "id": component['id']})
        url = rv_json['next']
        if not url:
            break
# save removed entries to json
    with open('deleted_pdc_entries.json', 'w') as fp:
        json.dump(packages, fp)
