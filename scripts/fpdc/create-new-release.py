""" create-new-release.py - Create a new release in FPDC.

http://fpdc...fedoraproject.org/api/v1/release

You can run this on your own machine and authenticate using your FAS credentials
You need to be a member of the releng FAS group to create new release.
"""

import argparse

from fpdc_client import FPDC, Release
from fpdc_client.base import STG_URL

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--releaseid",
    dest="releaseid",
    required=True,
    help="Name of the release (fedora-28, fedora-29, ..)",
)
parser.add_argument(
    "--name", dest="name", default="Fedora", help="Name of the product (Fedora, EPEL, ..)"
)
parser.add_argument(
    "--version", dest="version", required=True, help="Version (26, 27, ..)"
)
parser.add_argument(
    "--release-date",
    dest="releasedate",
    required=True,
    help="Date of the release (2017-11-14, ..)",
)
parser.add_argument(
    "--eol-date",
    dest="eoldate",
    required=True,
    help="Date of the release EOL (2018-11-30, ..)",
)
parser.add_argument("--sigkey", dest="sigkey", help="sigkey of the release")
parser.add_argument(
    "--staging", dest="staging", help="Use FPDC staging instance", action="store_true"
)

args = parser.parse_args()


if __name__ == "__main__":

    if args.staging:
        server = FPDC(url=STG_URL)
    else:
        server = FPDC()

    server.connect()
    server.login()

    new_release = Release.create(
        {
            "release_id": f"{args.releaseid}",
            "short": f"f{args.version}",
            "version": f"{args.version}",
            "name": f"{args.name}",
            "release_date": f"{args.releasedate}",
            "eol_date": f"{args.eoldate}",
            "sigkey": f"{args.sigkey}",
        }
    )

    print(f"Release created:\t\t {new_release['release_id']}")
    print(f"Release date:\t\t {new_release['release_date']}")
    print(f"Release eol:\t\t {new_release['eol_date']}")
    print(f"Release sigkey:\t\t {new_release['sigkey']}")
