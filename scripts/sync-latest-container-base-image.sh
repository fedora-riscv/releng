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
    -s  - Sync the stage registries instead of production
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

if ! [[ "${1}" =~ [31|32|33|34|35|36] ]];
then
    ARCHES=("aarch64" "armhfp" "ppc64le" "s390x" "x86_64")
else
    ARCHES=("aarch64" "ppc64le" "s390x" "x86_64")

fi
# This is the release of Fedora that is currently stable, it will define if we
# need to move the fedora:latest tag
current_stable="38"
# Define what is rawhide so we know to push that tag
current_rawhide="39"
# Sanity checking
# FIXME - Have to update this regex every time we drop a new Fedora Release
if ! [[ "${1}" =~ [31|32|33|34|35|36|37|38|39] ]];
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

if [[ ${1} -eq "$current_stable" ]]; then
    tagname="latest"
fi
if [[ ${1} -eq "$current_rawhide" ]]; then
    tagname="rawhide"
fi
if [[ -z "$stage" ]]; then
    registries=("registry.fedoraproject.org" "candidate-registry.fedoraproject.org" "quay.io/fedora")
else
    registries=("registry.stg.fedoraproject.org" "candidate-registry.stg.fedoraproject.org")
fi

# Copy a local image to all necessary remote registries
copy_image() {
    local src=$1; shift
    local name=$1; shift
    for registry in ${registries[@]}; do
        skopeo copy $src docker://${registry}/${name}
    done
}

# From already uploaded architecture-specific images, generate a manifest listed image
# on all registries
generate_manifest_list() {
    local name=$1; shift
    local version=$1; shift
    for registry in "${registries[@]}"
    do
        printf "Push manifest to ${registry}\n"
        if [ -n "$tagname" ]
        then
            printf "tag is set: ${tagname}\n"
            buildah rmi "${registry}/${name}:${tagname}" || true
            buildah manifest create "${registry}/${name}:${tagname}" "${ARCHES[@]/#/docker://${registry}/${name}:${version}-}"
            buildah manifest push "${registry}/${name}:${tagname}" "docker://${registry}/${name}:${tagname}" --all

        fi
        buildah rmi "${registry}/${name}:${version}" || true
        buildah manifest create "${registry}/${name}:${version}" "${ARCHES[@]/#/docker://${registry}/${name}:${version}-}"
        buildah manifest push "${registry}/${name}:${version}" "docker://${registry}/${name}:${version}" --all
    done
}

#
# Version should not be higher than rawhide
# Either there is a mistake or script is out of date
#
if [[ ${1} -gt "$current_rawhide" ]]; then
    printf "ERROR: VERSION HIGHER THAN RAWHIDE"
    exit 1
fi

if [[ -n ${build_name} ]]; then
    # Download the image
    work_dir=$(mktemp -d)
    pushd ${work_dir} &> /dev/null
    koji download-build --type=image  ${build_name}
    # Import the image
    for arch in "${ARCHES[@]}"; do
        xz -d ${build_name}.${arch}.tar.xz
        copy_image docker-archive:${build_name}.${arch}.tar fedora:${1}-${arch}
    done

    popd &> /dev/null

    generate_manifest_list fedora ${1}
    printf "Removing temporary directory\n"
    rm -rf $work_dir
fi
if [[ -n ${minimal_build_name} ]]; then
    # Download the image
    work_dir=$(mktemp -d)
    pushd ${work_dir} &> /dev/null
    koji download-build --type=image  ${minimal_build_name}
    # Import the image
    for arch in "${ARCHES[@]}"; do
        xz -d ${minimal_build_name}.${arch}.tar.xz
        copy_image docker-archive:${minimal_build_name}.${arch}.tar fedora-minimal:${1}-${arch}
    done
    popd &> /dev/null

    generate_manifest_list fedora-minimal ${1}

    printf "Removing temporary directory\n"
    rm -rf $work_dir
fi
