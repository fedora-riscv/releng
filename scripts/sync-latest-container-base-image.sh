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
f_clean_docker_images ()
{
    for i in $(sudo docker images -f 'dangling=true' -q);
    do
        sudo docker rmi $i;
    done
}
# This is the release of Fedora that is currently stable, it will define if we
# need to move the fedora:latest tag
current_stable="27"
# Define what is rawhide so we know to push that tag
current_rawhide="29"
# Sanity checking
# FIXME - Have to update this regex every time we drop a new Fedora Release
if ! [[ "${1}" =~ [24|25|26|27|28] ]];
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
# If ${stage} is a non-zero length string, then perform staging
if [[ -z "$stage" ]]; then
    # FIXME - switch to skopeo ASAP
    # Obtain the latest build
    #
    #   Need fXX-updates-canddiate to get actual latest nightly
    #
    build_name=$(koji -q latest-build --type=image f${1}-updates-candidate Fedora-Docker-Base | awk '{print $1}')
    minimal_build_name=$(koji -q latest-build --type=image f${1}-updates-candidate Fedora-Container-Minimal-Base | awk '{print $1}')
    if [[ -n ${build_name} ]]; then
        # Download the image
        work_dir=$(mktemp -d)
        pushd ${work_dir} &> /dev/null
            koji download-build --type=image --arch=x86_64 ${build_name}
            # Import the image
            if sudo docker load -i ${build_name}.x86_64.tar.xz; then
                image_name=$(printf "${build_name}" | awk '{print tolower($0) ".x86_64" }')
            fi
        popd &> /dev/null
        # If something went wrong, the value of ${image_name} would be an empty string,
        # so make sure it isn't
        if [[ -n "${image_name}" ]]; then
            sudo docker tag ${image_name} registry.fedoraproject.org/fedora:${1}
            sudo docker push registry.fedoraproject.org/fedora:${1}
            sudo docker tag ${image_name} candidate-registry.fedoraproject.org/fedora:${1}
            sudo docker push candidate-registry.fedoraproject.org/fedora:${1}
            if [[ ${1} -eq "$current_stable" ]]; then
                sudo docker tag ${image_name} registry.fedoraproject.org/fedora:latest
                sudo docker push registry.fedoraproject.org/fedora:latest
                sudo docker tag ${image_name} candidate-registry.fedoraproject.org/fedora:latest
                sudo docker push candidate-registry.fedoraproject.org/fedora:latest
            fi
            if [[ ${1} -eq "$current_rawhide" ]]; then
                sudo docker tag ${image_name} registry.fedoraproject.org/fedora:rawhide
                sudo docker push registry.fedoraproject.org/fedora:rawhide
                sudo docker tag ${image_name} candidate-registry.fedoraproject.org/fedora:rawhide
                sudo docker push candidate-registry.fedoraproject.org/fedora:rawhide
            fi
            f_clean_docker_images
        else
            printf "ERROR: Unable to import image\n"
            exit 2
        fi
    fi
    if [[ -n ${minimal_build_name} ]]; then
        # Download the image
        work_dir=$(mktemp -d)
        pushd ${work_dir} &> /dev/null
            koji download-build --type=image --arch=x86_64 ${minimal_build_name}
            # Import the image
            if sudo docker load -i ${minimal_build_name}.x86_64.tar.xz; then
                min_image_name=$(printf "${minimal_build_name}" | awk '{print tolower($0) ".x86_64" }')
            fi
        popd &> /dev/null
        # If something went wrong, the value of ${image_name} would be an empty string,
        # so make sure it isn't
        if [[ -n "${min_image_name}" ]]; then
            sudo docker tag ${min_image_name} registry.fedoraproject.org/fedora-minimal:${1}
            sudo docker push registry.fedoraproject.org/fedora-minimal:${1}
            sudo docker tag ${min_image_name} candidate-registry.fedoraproject.org/fedora-minimal:${1}
            sudo docker push candidate-registry.fedoraproject.org/fedora-minimal:${1}
            if [[ ${1} -eq "$current_stable" ]]; then
                sudo docker tag ${min_image_name} registry.fedoraproject.org/fedora-minimal:latest
                sudo docker push registry.fedoraproject.org/fedora-minimal:latest
                sudo docker tag ${min_image_name} candidate-registry.fedoraproject.org/fedora-minimal:latest
                sudo docker push candidate-registry.fedoraproject.org/fedora-minimal:latest
            fi
            if [[ ${1} -eq "$current_rawhide" ]]; then
                sudo docker tag ${min_image_name} registry.fedoraproject.org/fedora-minimal:rawhide
                sudo docker push registry.fedoraproject.org/fedora-minimal:rawhide
                sudo docker tag ${min_image_name} candidate-registry.fedoraproject.org/fedora-minimal:rawhide
                sudo docker push candidate-registry.fedoraproject.org/fedora-minimal:rawhide
            fi
            f_clean_docker_images
        else
            printf "ERROR: Unable to import image\n"
            exit 2
        fi
    fi
else
    # For stage, we only mirror what's in production.
    printf "Skopeo syncing registry.stg.fedoraproject.org/fedora:${1} ...\n"
    sudo skopeo copy \
        --src-cert-dir /etc/docker/certs.d/registry.stg.fedoraproject.org/ \
        --dest-cert-dir /etc/docker/certs.d/candidate-registry.stg.fedoraproject.org/ \
        docker://registry.fedoraproject.org/fedora:${1} \
        docker://registry.stg.fedoraproject.org/fedora:${1}
    printf "Skopeo syncing candidate-registry.stg.fedoraproject.org/fedora:${1} ...\n"
    sudo skopeo copy \
        --src-cert-dir /etc/docker/certs.d/registry.stg.fedoraproject.org/ \
        --dest-cert-dir /etc/docker/certs.d/candidate-registry.stg.fedoraproject.org/ \
        docker://registry.fedoraproject.org/fedora:${1} \
        docker://candidate-registry.stg.fedoraproject.org/fedora:${1}
    if [[ ${1} -eq "$current_stable" ]]; then
        printf "Skopeo syncing registry.stg.fedoraproject.org/fedora:latest ...\n"
        sudo skopeo copy \
            --src-cert-dir /etc/docker/certs.d/registry.stg.fedoraproject.org/ \
            --dest-cert-dir /etc/docker/certs.d/candidate-registry.stg.fedoraproject.org/ \
            docker://registry.fedoraproject.org/fedora:${1} \
            docker://registry.stg.fedoraproject.org/fedora:latest
        printf "Skopeo syncing candidate-registry.stg.fedoraproject.org/fedora:latest ...\n"
        sudo skopeo copy \
            --src-cert-dir /etc/docker/certs.d/registry.stg.fedoraproject.org/ \
            --dest-cert-dir /etc/docker/certs.d/candidate-registry.stg.fedoraproject.org/ \
            docker://registry.fedoraproject.org/fedora:${1} \
            docker://candidate-registry.stg.fedoraproject.org/fedora:latest
    fi
    if [[ ${1} -eq "$current_rawhide" ]]; then
        printf "Skopeo syncing registry.stg.fedoraproject.org/fedora:rawhide ...\n"
        sudo skopeo copy \
            --src-cert-dir /etc/docker/certs.d/registry.stg.fedoraproject.org/ \
            --dest-cert-dir /etc/docker/certs.d/candidate-registry.stg.fedoraproject.org/ \
            docker://registry.fedoraproject.org/fedora:${1} \
            docker://registry.stg.fedoraproject.org/fedora:latest
        printf "Skopeo syncing candidate-registry.stg.fedoraproject.org/fedora:rawhide ...\n"
        sudo skopeo copy \
            --src-cert-dir /etc/docker/certs.d/registry.stg.fedoraproject.org/ \
            --dest-cert-dir /etc/docker/certs.d/candidate-registry.stg.fedoraproject.org/ \
            docker://registry.fedoraproject.org/fedora:${1} \
            docker://candidate-registry.stg.fedoraproject.org/fedora:latest
    fi
fi
