""" create-product-version.py - Create a new "product version" in PDC.

https://pdc..fedoraproject.org/rest_api/v1/product-versions/

Product versions are used by Greenwave to identify gating criteria.

You can run this on pdc-backend01, the token is in /etc/pdc.d/
You can also find the token in the private git repo.
"""

import argparse

import pdc_client

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('servername', help='PDC server name.  See /etc/pdc.d/')
parser.add_argument('token', help='PDC token for authentication.')
parser.add_argument('product', help='Name of the product')
parser.add_argument('version', help='Version (26, 27, ..)')

args = parser.parse_args()


if __name__ == '__main__':
    print("Connecting to PDC args.server %r with token %r" % (args.servername, args.token))
    pdc = pdc_client.PDCClient(args.servername, token=args.token)

    pdc['product-versions']._(dict(
        name='%s %s' % (args.product, args.version),
        product=args.product,
        short=args.product.lower(),
        version=args.version,
    ))
    pdc['releases']._(dict(
        name=args.product,
        short=args.product.lower(),
        version=args.version,
        release_type='ga',
        product_version='%s-%s' % (args.product, args.version),
    ))
