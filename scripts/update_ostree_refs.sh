#!/usr/bin/bash

N=$1
ARCHES='aarch64 ppc64le x86_64'
VARIANTS='silverblue kinoite sericea onyx'
OSTREE_COMPOSE_BASEDIR='/mnt/koji/compose/ostree/repo'
OSTREE_REPO_BASEDIR='/mnt/koji/ostree/repo/'

function do_things() {
for variant in $VARIANTS; do
    for arch in $ARCHES; do
        # First create the new updates ref based on the main ref, which had been created from from branched composes
        sudo -u ftpsync ostree refs --create="fedora/${N}/${arch}/updates/${variant}" "fedora/${N}/${arch}/${variant}"
        # Then delete the main ref
        sudo ostree refs --delete "fedora/${N}/${arch}/${variant}"
        # Then create a new main ref that is an alias to the updates ref
        sudo -u ftpsync ostree refs --alias --create="fedora/${N}/${arch}/${variant}" "fedora/${N}/${arch}/updates/${variant}"
     done
 done
}

pushd $OSTREE_COMPOSE_BASEDIR
do_things
popd

pushd $OSTREE_REPO_BASEDIR
do_things
popd

pushd $OSTREE_REPO_BASEDIR
sudo ostree summary -u
popd