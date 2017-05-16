#!/usr/bin/env python
""" koji-module-info.py  -  Find info about modules associated with builds.

    Usage:  koji-module-info.py $BUILD_ID

At the moment, it requires that the module is completed and builds have been tagged.

"""

import sys

import arrow
import koji
import requests

buildid = int(sys.argv[-1])

mbs_search_url = 'https://mbs.fedoraproject.org/module-build-service/1/module-builds/?koji_tag=%s&verbose=true'
mbs_specifics_url = 'https://mbs.fedoraproject.org/module-build-service/1/module-builds/%s?verbose=true'

session = koji.ClientSession('https://koji.fedoraproject.org/kojihub')
tags = session.listTags(build=buildid)
tags = [tag['name'] for tag in tags]
tags = [tag for tag in tags if not tag.endswith('-build')]

if not tags:
    print("Build %r is not associated with any tags." % buildid)
    print("Bother threebean to finish this:  https://pagure.io/fm-orchestrator/issue/375")"
    sys.exit(1)

for tag in tags:
    response = requests.get(mbs_search_url % tag)
    if not bool(response):
        print("Failed to talk to %r, %r" % (response.url, response))
        sys.exit(1)

    data = response.json()
    if len(data['items']) > 1:
        print("Tag %s appears to be associated with %i modules." % (
            tag, len(data['items'])))
        continue
    elif len(data['items']) < 1:
        print("Tag %s is not associated with any modules." % tag)
        continue

    detail = data['items'][0]
    timestamp = arrow.get(detail['time_submitted'])
    response = requests.get(mbs_specifics_url % detail['id'])
    data = response.json()
    print("{koji_tag} is for {name}-{stream}-{version},\n\t"
          "submitted {ago} by @{owner}\n\t"
          "'{state_name}': {state_reason}\n\t"
          "{url}\n".format(url=response.url, ago=timestamp.humanize(), **data))
