""" create-product.py - Create a new "product" in PDC.

https://pdc..fedoraproject.org/rest_api/v1/products/

We will almost always only have one product:  "Fedora".

You can run this on pdc-backend01, the token is in /etc/pdc.d/
You can also find the token in the private git repo.
"""

import argparse

import pdc_client

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('servername', help='PDC server name.  See /etc/pdc.d/')
parser.add_argument('token', help='PDC token for authentication.')
parser.add_argument('short', help='Short identifier for the product.')
parser.add_argument('name', help='Name of the product.')

args = parser.parse_args()


if __name__ == '__main__':
    print("Connecting to PDC args.server %r with token %r" % (args.servername, args.token))
    pdc = pdc_client.PDCClient(args.servername, token=args.token)

    pdc['products']._(dict(
        name=args.name,
        short=args.short,
    ))
