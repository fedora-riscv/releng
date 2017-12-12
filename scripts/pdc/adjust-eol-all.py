"""
This script will change the EOL of a branch in pdc under
https://pdc.fedoraproject.org/rest_api/v1/component-branches-slas/ api.

This script can be used when EOL of a release gets changed because of
delays in the releases.
"""

import requests
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('token', help='PDC token for authentication.')                                                
parser.add_argument('branch', help='Name of the branch (f26, or 1.12, or master)')                                
parser.add_argument('eol', help='End of life date for the SLAs, '                                                 
'in the format of "2020-01-01".')
parser.add_argument('stg', help='Use Staging PDC', default = False)

args = parser.parse_args()

if __name__ == '__main__':
    token = args.token 
    eol_date = args.eol
    branch = args.branch
    if args.stg:
        pdc = 'https://pdc.stg.fedoraproject.org/'
    else:
        pdc = 'https://pdc.fedoraproject.org/'
    sla_ids = set()
    url = '{0}/rest_api/v1/component-branch-slas/?page_size=100&branch={1}'.format(pdc,branch)
    while True:
        rv = requests.get(url)
        if not rv.ok:
            raise RuntimeError('Failed with: {0}'.format(rv.text))
        rv_json = rv.json()
        for sla in rv_json['results']:
            sla_ids.add(sla['id'])
        url = rv_json['next']
        if not url:
            break
    eol_data = json.dumps({'eol': eol_date})
    headers = {'Content-Type': 'application/json', 'Authorization': 'token {0}'.format(token)}
    for sla_id in sla_ids:
        sla_url = '{0}/rest_api/v1/component-branch-slas/{1}/'.format(pdc,sla_id)
        print(sla_url)
        rv = requests.patch(sla_url, headers=headers, data=eol_data)
        if not rv.ok:
            raise RuntimeError('Failed with: {0}'.format(rv.text))

