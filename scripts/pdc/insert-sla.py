""" insert-sla.py - Add a new branch SLA to PDC.

https://pdc.fedoraproject.org/rest_api/v1/component-sla-types/

Branches in dist-git may have arbitrary EOLs and SLAs, but the SLAs must be
chosen from a set specified by release-engineering.

You can run this on pdc-backend01, the token is in /etc/pdc.d/
You can also find the token in the private git repo.
"""

import os
import sys

import pdc_client

servername, token = sys.argv[-2], sys.argv[-1]

if os.path.basename(__file__) in (servername, token,):
    raise ValueError("Provide a PDC server name defined in /etc/pdc.d/ and a token")

print("Connecting to PDC server %r with token %r" % (servername, token))
pdc = pdc_client.PDCClient(servername, token=token)

name = raw_input("Name of the SLA: ")
description = raw_input("Description of the SLA: ")

entry = dict(name=name, description=description)

print("Submitting POST.")
pdc['component-sla-types']._(entry)
print("Done.")
