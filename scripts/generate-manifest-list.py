#!/usr/bin/python3
#
# generate-manifest-list.py - A script used to create and push the container base image
#                             manifest list used for mutli arch support
#                             This is used by sync-latest-container-base-image.sh script
#
# Authors:
#    Clement Verna <cverna@fedoraproject.org>
# Copyright (C) 2018 Red Hat Inc,
# SPDX-License-Identifier:	GPL-2.0+
import argparse
import json
from functools import wraps

import requests


MEDIA_TYPE_LIST_V2 = "application/vnd.docker.distribution.manifest.list.v2+json"

MANIFEST_LIST = {"schemaVersion": 2, "mediaType": MEDIA_TYPE_LIST_V2, "manifests": []}

ARCHES = ["x86_64", "aarch64", "armhfp", "ppc64le", "s390x"]


def certs(function):
    """ Decorator that create the certificate path based
    on the registry name """

    @wraps(function)
    def get_certs_path(*args, **kwargs):
        cert_path = f"/etc/docker/certs.d/{kwargs['registry']}/client.cert"
        cert_key = f"/etc/docker/certs.d/{kwargs['registry']}/client.key"
        kwargs["cert"] = (cert_path, cert_key)
        return function(*args, **kwargs)

    return get_certs_path


@certs
def create_image_manifest(tag, name, registry, cert):
    """ Get the manifest for a specific image and returns the data
    needed to build the manifest list """

    image = None
    headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
    res = requests.get(
        f"https://{registry}/v2/{name}/manifests/{tag}", cert=cert, headers=headers
    )

    if res.ok:
        data = res.json()
        image = {
            "mediaType": res.headers["Content-Type"],
            "size": int(res.headers["Content-Length"]),
            "digest": res.headers["Docker-Content-Digest"],
            "platform": {"architecture": "", "os": "linux"},
        }

    return image


@certs
def push_manifest_list(manifest_list, tags, name, registry, cert):
    """ Push the manifest list to the correct tags """

    headers = {"Content-Type": MEDIA_TYPE_LIST_V2}

    for tag in tags:
        res = requests.put(
            f"https://{registry}/v2/{name}/manifests/{tag}",
            data=json.dumps(manifest_list),
            headers=headers,
            cert=cert,
        )

        if not res.ok:
            print(f"ERROR: Failed to push the manifest list : {res.text}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--release", "-r", help="number of the fedora release", required=True
    )
    parser.add_argument(
        "--registry",
        help="name of the container registry",
        default="registry.fedoraproject.org",
    )
    parser.add_argument(
        "--tag", help="tag to apply to the container image", default="latest"
    )
    parser.add_argument("--image", help="name of the container image", default="fedora")
    args = parser.parse_args()

    tags = [f"{args.release}-" + arch for arch in ARCHES]

    for tag in tags:
        image = create_image_manifest(tag=tag, name=args.image, registry=args.registry)
        if image is not None:
            manifest = image.copy()
            if "x86_64" in tag:
                manifest["platform"]["architecture"] = "amd64"
            else:
                manifest["platform"]["architecture"] = tag[3:]
            MANIFEST_LIST["manifests"].append(manifest)
        else:
            print(f"ERROR : Could not find the image manifest for fedora:{tag}")

    push_manifest_list(
        manifest_list=MANIFEST_LIST,
        tags=[args.release, args.tag],
        name=args.image,
        registry=args.registry,
    )
