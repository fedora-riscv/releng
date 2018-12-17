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

ARCHES=("aarch64" "armhfp" "ppc64le" "s390x" "x86_64")
# This is the release of Fedora that is currently stable, it will define if we
# need to move the fedora:latest tag
current_stable="29"
# Define what is rawhide so we know to push that tag
current_rawhide="30"
# Sanity checking
# FIXME - Have to update this regex every time we drop a new Fedora Release
if ! [[ "${1}" =~ [24|25|26|27|28|29|30] ]];
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

if [[ ${1} -eq "$current_stable" ]]; then
    tagname="latest"
fi
if [[ ${1} -eq "$current_rawhide" ]]; then
    tagname="rawhide"
fi

minimal_build_name=$(koji -q latest-build --type=image f${1}-updates-candidate Fedora-Container-Minimal-Base | awk '{print $1}')
if [[ -n ${build_name} ]]; then
    # Download the image
    work_dir=$(mktemp -d)
    pushd ${work_dir} &> /dev/null
    koji download-build --type=image  ${build_name}
    # Import the image
    for arch in "${ARCHES[@]}"
    do
        xz -d ${build_name}.${arch}.tar.xz
        # If ${stage} is a non-zero length string, then perform staging
        if [[ -z "$stage" ]]; then
            registries=("registry.fedoraproject.org" "candidate-registry.fedoraproject.org")
            skopeo copy docker-archive:${build_name}.${arch}.tar docker://registry.fedoraproject.org/fedora:${1}-${arch}
            skopeo copy docker-archive:${build_name}.${arch}.tar docker://candidate-registry.fedoraproject.org/fedora:${1}-${arch}
            skopeo copy docker-archive:${build_name}.${arch}.tar docker://quay.io/fedora/fedora:${1}-${arch}
        else
            registries=("registry.stg.fedoraproject.org" "candidate-registry.stg.fedoraproject.org")
            skopeo copy docker-archive:${build_name}.${arch}.tar docker://registry.stg.fedoraproject.org/fedora:${1}-${arch}
            skopeo copy docker-archive:${build_name}.${arch}.tar docker://candidate-registry.stg.fedoraproject.org/fedora:${1}-${arch}
        fi
    done

    popd &> /dev/null

    for registry in "${registries[@]}"
    do
        printf "Push manifest to ${registry}\n"
        if [ -z "$tagname" ]
        then
            printf "tag is not set: ${tagname}\n"
            python3 generate-manifest-list.py -r ${1} --registry ${registry} --image fedora
        else
            printf "tag is set: ${tagname}\n"
            python3 generate-manifest-list.py -r ${1} --registry ${registry} --tag ${tagname} --image fedora
        fi
    done
    printf "Removing temporary directory\n"
    rm -rf $work_dir
fi
if [[ -n ${minimal_build_name} ]]; then
    # Download the image
    work_dir=$(mktemp -d)
    pushd ${work_dir} &> /dev/null
    koji download-build --type=image  ${minimal_build_name}
    # Import the image
    for arch in "${ARCHES[@]}"
    do
        xz -d ${minimal_build_name}.${arch}.tar.xz
        # If ${stage} is a non-zero length string, then perform staging
        if [[ -z "$stage" ]]; then
            registries=("registry.fedoraproject.org" "candidate-registry.fedoraproject.org")
            skopeo copy docker-archive:${minimal_build_name}.${arch}.tar docker://registry.fedoraproject.org/fedora-minimal:${1}-${arch}
            skopeo copy docker-archive:${minimal_build_name}.${arch}.tar docker://candidate-registry.fedoraproject.org/fedora-minimal:${1}-${arch}
        else
            registries=("registry.stg.fedoraproject.org" "candidate-registry.stg.fedoraproject.org")
            skopeo copy docker-archive:${minimal_build_name}.${arch}.tar docker://registry.stg.fedoraproject.org/fedora-minimal:${1}-${arch}
            skopeo copy docker-archive:${minimal_build_name}.${arch}.tar docker://candidate-registry.stg.fedoraproject.org/fedora-minimal:${1}-${arch}
            skopeo copy docker-archive:${minimal_build_name}.${arch}.tar docker://quay.io/fedora/fedora-minimal:${1}-${arch}
        fi
     done
     popd &> /dev/null

     for registry in "${registries[@]}"
     do
         printf "Push manifest to ${registry}\n"
         if [ -z "$tagname" ]
         then
             printf "tag is not set: ${tagname}\n"
             python3 generate-manifest-list.py -r ${1} --registry ${registry} --image fedora-minimal
         else
             printf "tag is set: ${tagname}\n"
             python3 generate-manifest-list.py -r ${1} --registry ${registry} --tag ${tagname} --image fedora-minimal
         fi
     done

     printf "Removing temporary directory\n"
     rm -rf $work_dir

fi
