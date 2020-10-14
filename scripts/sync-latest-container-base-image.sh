#!/bin/bash
#
# Sync latest docker image
#
# Docs in the f_help function
f_ctrl_c() {
    printf "\n*** Exiting ***\n"
    exit $?
}
# trap int (ctrl-c)
trap f_ctrl_c SIGINT
f_help() {
    cat <<EOF
NAME
    ${0}
SYNOPSIS
    ${0} FEDORA_RELEASE IMAGE_URL [-s]
OPTIONS
    -s  - Sync the production and stage registries.
DESCRIPTION
    This is a stop-gap solution to identify parent inheritance of container
    images until the container release automation[0] is in place and we have
    fully automated rebuilds[1] in OSBS.
    This information should be used such that the images can be rebuilt and
    released in the appropriate order using flr-koji.
[0] - https://pagure.io/releng-automation
[1] - https://osbs.readthedocs.io/en/latest/multiarch.html#chain-rebuilds
EXAMPLE
    ${0} 26
EOF
}

ARCHES=("aarch64" "armhfp" "ppc64le" "s390x" "x86_64")
# This is the release of Fedora that is currently stable, it will define if we
# need to move the fedora:latest tag
current_stable="33"
# Define what is rawhide so we know to push that tag
current_rawhide="34"
# Sanity checking
# FIXME - Have to update this regex every time we drop a new Fedora Release
if ! [[ "${1}" =~ [24|25|26|27|28|29|30|31] ]];
then
    printf "ERROR: FEDORA_RELEASE missing or invalid\n"
    f_help
    exit 1
fi
# Determine if we want stage or not (yes, I know this should be getops but I
# don't want this script to survive so we're doing quick and dirty.
#
# If ${stage} is a non-zero length string, then perform staging
stage=""
if [[ "${2}" == "-s" ]]; then
    printf "INFO: PERFORMING STAGE SYNC\n"
    stage="true"
fi
# Obtain the latest build
#
#   Need fXX-updates-canddiate to get actual latest nightly
#
build_name=$(koji -q latest-build --type=image f${1}-updates-candidate Fedora-Container-Base | awk '{print $1}')
minimal_build_name=$(koji -q latest-build --type=image f${1}-updates-candidate Fedora-Container-Minimal-Base | awk '{print $1}')

#Push the base image
if [[ -n ${build_name} ]]; then

    # Download the image
    work_dir=$(mktemp -d)
    pushd ${work_dir} &> /dev/null
    koji download-build --type=image  ${build_name}

    # Create the manifest list for multi-arch support
    podman manifest create registry.fedoraproject.org/fedora:${1}
    podman manifest create candidate-registry.fedoraproject.org/fedora:${1}
    podman manifest create quay.io/fedora/fedora:${1}

    # Import the image
    for arch in "${ARCHES[@]}"
    do
        xz -d ${build_name}.${arch}.tar.xz
        skopeo copy docker-archive:${build_name}.${arch}.tar docker://registry.fedoraproject.org/fedora:${1}-${arch}
        skopeo copy docker-archive:${build_name}.${arch}.tar docker://candidate-registry.fedoraproject.org/fedora:${1}-${arch}
        skopeo copy docker-archive:${build_name}.${arch}.tar docker://quay.io/fedora/fedora:${1}-${arch}
        podman manifest add registry.fedoraproject.org/fedora:${1} docker://registry.fedoraproject.org/fedora:${1}-${arch}
        podman manifest add candidate-registry.fedoraproject.org/fedora:${1} docker://candidate-registry.fedoraproject.org/fedora:${1}-${arch}
        podman manifest add quay.io/fedora/fedora:${1} docker://quay.io/fedora/fedora:${1}-${arch}
    done
    popd &> /dev/null

    podman manifest push registry.fedoraproject.org/fedora:${1} docker://registry.fedoraproject.org/fedora:${1}
    podman manifest push candidate-registry.fedoraproject.org/fedora:${1} docker://candidate-registry.fedoraproject.org/fedora:${1}
    podman manifest push quay.io/fedora/fedora:${1} docker://quay.io/fedora/fedora:${1}

    # Create the latest tag
    if [[ ${1} -eq "$current_stable" ]]; then
        skopeo copy --all docker://registry.fedoraproject.org/fedora:${1} docker://registry.fedoraproject.org/fedora:latest
        skopeo copy --all docker://candidate-registry.fedoraproject.org/fedora:${1} docker://candidate-registry.fedoraproject.org/fedora:latest
        skopeo copy --all docker://quay.io/fedora/fedora:${1} docker://quay.io/fedora/fedora:latest
    fi
    # Create the rawhide tag
    if [[ ${1} -eq "$current_rawhide" ]]; then
        skopeo copy --all docker://registry.fedoraproject.org/fedora:${1} docker://registry.fedoraproject.org/fedora:rawhide
        skopeo copy --all docker://candidate-registry.fedoraproject.org/fedora:${1} docker://candidate-registry.fedoraproject.org/fedora:rawhide
        skopeo copy --all docker://quay.io/fedora/fedora:${1} docker://quay.io/fedora/fedora:rawhide
    fi

    # Copy the images in staging
    if ! [[ -z "$stage" ]]; then
        skopeo copy --all docker://registry.fedoraproject.org/fedora:${1} docker://registry.stg.fedoraproject.org/fedora:${1}
        skopeo copy --all docker://candidate-registry.fedoraproject.org/fedora:${1} docker://create candidate-registry.stg.fedoraproject.org/fedora:${1}

        if [[ ${1} -eq "$current_stable" ]]; then
            skopeo copy --all docker://registry.stg.fedoraproject.org/fedora:${1} docker://registry.stg.fedoraproject.org/fedora:latest
            skopeo copy --all docker://candidate-registry.stg.fedoraproject.org/fedora:${1} docker://candidate-registry.stg.fedoraproject.org/fedora:latest
        fi
        if [[ ${1} -eq "$current_rawhide" ]]; then
            skopeo copy --all docker://registry.stg.fedoraproject.org/fedora:${1} docker://registry.stg.fedoraproject.org/fedora:rawhide
            skopeo copy --all docker://candidate-registry.stg.fedoraproject.org/fedora:${1} docker://candidate-registry.stg.fedoraproject.org/fedora:latest
        fi
    fi
    printf "Removing temporary directory\n"
    rm -rf $work_dir
    podman rmi -f registry.fedoraproject.org/fedora:${1}
    podman rmi -f candidate-registry.fedoraproject.org/fedora:${1}
    podman rmi -f quay.io/fedora/fedora:${1}
fi

#Push the minimal base image
if [[ -n ${minimal_build_name} ]]; then
    # Download the image
    work_dir=$(mktemp -d)
    pushd ${work_dir} &> /dev/null
    koji download-build --type=image  ${minimal_build_name}

    # Create the manifest list for multi-arch support
    podman manifest create registry.fedoraproject.org/fedora-minimal:${1}
    podman manifest create candidate-registry.fedoraproject.org/fedora-minimal:${1}
    podman manifest create quay.io/fedora/fedora-minimal:${1}

    # Import the image
    for arch in "${ARCHES[@]}"
    do
        xz -d ${minimal_build_name}.${arch}.tar.xz
        skopeo copy docker-archive:${minimal_build_name}.${arch}.tar docker://registry.fedoraproject.org/fedora-minimal:${1}-${arch}
        skopeo copy docker-archive:${minimal_build_name}.${arch}.tar docker://candidate-registry.fedoraproject.org/fedora-minimal:${1}-${arch}
        skopeo copy docker-archive:${minimal_build_name}.${arch}.tar docker://quay.io/fedora/fedora-minimal:${1}-${arch}
        podman manifest add registry.fedoraproject.org/fedora-minimal:${1} docker://registry.fedoraproject.org/fedora-minimal:${1}-${arch}
        podman manifest add candidate-registry.fedoraproject.org/fedora-minimal:${1} docker://candidate-registry.fedoraproject.org/fedora-minimal:${1}-${arch}
        podman manifest add quay.io/fedora/fedora-minimal:${1} docker://quay.io/fedora/fedora-minimal:${1}-${arch}

     done
     popd &> /dev/null

    podman manifest push registry.fedoraproject.org/fedora-minimal:${1} docker://registry.fedoraproject.org/fedora-minimal:${1}
    podman manifest push candidate-registry.fedoraproject.org/fedora-minimal:${1} docker://candidate-registry.fedoraproject.org/fedora-minimal:${1}
    podman manifest push quay.io/fedora/fedora-minimal:${1} docker://quay.io/fedora/fedora-minimal:${1}

    # Create the latest tag
    if [[ ${1} -eq "$current_stable" ]]; then
        skopeo copy --all docker://registry.fedoraproject.org/fedora-minimal:${1} docker://registry.fedoraproject.org/fedora-minimal:latest
        skopeo copy --all docker://candidate-registry.fedoraproject.org/fedora-minimal:${1} docker://candidate-registry.fedoraproject.org/fedora-minimal:latest
        skopeo copy --all docker://quay.io/fedora/fedora-minimal:${1} docker://quay.io/fedora/fedora-minimal:latest
    fi
    # Create the rawhide tag
    if [[ ${1} -eq "$current_rawhide" ]]; then
        skopeo copy --all docker://registry.fedoraproject.org/fedora-minimal:${1} docker://registry.fedoraproject.org/fedora-minimal:rawhide
        skopeo copy --all docker://candidate-registry.fedoraproject.org/fedora-minimal:${1} docker://candidate-registry.fedoraproject.org/fedora-minimal:rawhide
        skopeo copy --all docker://quay.io/fedora/fedora-minimal:${1} docker://quay.io/fedora/fedora-minimal:rawhide
    fi

    # Copy the images in staging
    if ! [[ -z "$stage" ]]; then
        skopeo copy --all docker://registry.fedoraproject.org/fedora-minimal:${1} docker://registry.stg.fedoraproject.org/fedora-minimal:${1}
        skopeo copy --all docker://candidate-registry.fedoraproject.org/fedora-minimal:${1} docker://create candidate-registry.stg.fedoraproject.org/fedora-minimal:${1}

        if [[ ${1} -eq "$current_stable" ]]; then
            skopeo copy --all docker://registry.stg.fedoraproject.org/fedora-minimal:${1} docker://registry.stg.fedoraproject.org/fedora-minimal:latest
            skopeo copy --all docker://candidate-registry.stg.fedoraproject.org/fedora-minimal:${1} docker://candidate-registry.stg.fedoraproject.org/fedora-minimal:latest
        fi
        if [[ ${1} -eq "$current_rawhide" ]]; then
            skopeo copy --all docker://registry.stg.fedoraproject.org/fedora-minimal:${1} docker://registry.stg.fedoraproject.org/fedora-minimal:rawhide
            skopeo copy --all docker://candidate-registry.stg.fedoraproject.org/fedora-minimal:${1} docker://candidate-registry.stg.fedoraproject.org/fedora-minimal:latest
        fi
    fi

     printf "Removing temporary directory\n"
     rm -rf $work_dir
     podman rmi -f registry.fedoraproject.org/fedora-minimal:${1}
     podman rmi -f candidate-registry.fedoraproject.org/fedora-minimal:${1}
     podman rmi -f quay.io/fedora/fedora-minimal:${1}
fi
