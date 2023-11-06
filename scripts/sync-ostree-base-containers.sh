#!/bin/bash

set -euo pipefail

# Poll the Fedora OSTree repository and convert the silverblue and kinoite refs
# to container images.

# Execute a command verbosely, i.e. echoing its arguments to stderr
runv () {
    ( set -x ; $@ )
}

fedora_version=${1}
shift

ARCHES=("x86_64" "aarch64" "ppc64le")
# This is the release of Fedora that is currently stable, it will define if we
# need to move the fedora:latest tag
current_stable="39"
# Define what is rawhide so we know to push that tag
current_rawhide="40"

ostree_base_images=(silverblue kinoite sericea)

# An optional additional alias for the image; this is only set for current stable and rawhide.
# For example, given current_stable=36, then the previous release of 35 will just appear as a single
# fedora-silverblue:35 image, whereas 36 will appear as fedora-silverblue:36 *and* fedora-silverblue:latest.
# Rawhide is also a special case.
tagname=
if [[ ${fedora_version} -eq "$current_stable" ]]; then
    tagname="latest"
fi
if [[ ${fedora_version} -eq "$current_rawhide" ]]; then
    tagname="rawhide"
    # Confusingly, the ostree repository seems not to have an alias for 39, and wants "rawhide" today,
    # so we are effectively backreferencing that.  This may be a releng bug.
    ostree_version_component="rawhide"
else
    ostree_version_component="${fedora_version}"
fi
if [[ -z "${REGISTRY_STAGE:-}" ]]; then
    registries=("registry.fedoraproject.org" "candidate-registry.fedoraproject.org" "quay.io/fedora")
else
    registries=("registry.stg.fedoraproject.org" "candidate-registry.stg.fedoraproject.org")
fi
canonical_registry=${registries[-1]}
secondary_registries=(${registries[@]})
unset secondary_registries[-1]

arch_to_goarch() {
    local a=$1; shift
    # See https://github.com/coreos/stream-metadata-go/blob/c5fe1b98ac1b1e6ab62a606b7580dc1f30703f83/arch/arch.go#L14
    case "$a" in
        aarch64) echo arm64 ;;
        x86_64) echo amd64 ;;
        *) echo $a ;;
    esac
}

work_tmpdir=$(mktemp -d -p /var/tmp --suffix=.sync-ostree)
cleanup() {
    rm -rf "${work_tmpdir}"
}
trap cleanup EXIT
cd "${work_tmpdir}"

for name in "${ostree_base_images[@]}"; do
    echo "Processing: ${name}"
    # The base name component, e.g. "fedora-silverblue"
    imgname=fedora-"${name}"
    # This will be e.g. fedora-silverblue:37 - it always uses a numbered version
    imgtag=${imgname}:${fedora_version}
    # This is the full expanded canonical image, e.g. quay.io/fedora/fedora-silverblue:37
    primary_imgtag=${canonical_registry}/${imgtag}
    # aliased_name is e.g. fedora-silverblue:latest instead of fedora-silverblue:37 (if 37 is current stable)
    aliased_name=
    # This is only non-empty if tagname is set.
    if test -n "${tagname}"; then
        aliased_name=${imgname}:${tagname}
    fi

    mkdir $name
    pushd $name &> /dev/null
    # Note that this command will use the current architecture
    arch=$(arch)
    if ! runv skopeo inspect -n docker://${primary_imgtag} > inspect.json; then
        echo "Failed to invoke skopeo, assuming container does not exist"
    fi
    container_commit=
    if test -s inspect.json; then
        container_commit=$(jq -r '.Labels["ostree.commit"]' inspect.json)
    fi
    mkdir repo
    ostree --repo=repo init --mode=bare-user
    echo fsync=0 >> repo/config
    if test -f /etc/ostree/remotes.d/fedora.conf; then
        cat /etc/ostree/remotes.d/fedora.conf >> repo/config
    else
        cat >> repo/config <<'EOF'
[remote "fedora"]
url=https://ostree.fedoraproject.org
gpg-verify=true
gpgkeypath=/etc/pki/rpm-gpg/
contenturl=mirrorlist=https://ostree.fedoraproject.org/mirrorlist
EOF
    fi
    ostree_ref=fedora:fedora/${ostree_version_component}/${arch}/${name}
    runv ostree --repo=repo pull --commit-metadata-only $ostree_ref
    current_commit=$(ostree --repo=repo rev-parse $ostree_ref)
    echo "current ${ostree_ref}: $current_commit"
    echo "current ${arch} container image ${imgtag}: $container_commit"
    # IMPORTANT: We want to no-op if the sync is already done, otherwise we'll end up
    # regenerating the image, which can cause people to apply pointless updates.
    # This logic here is a bit hacky because we're only querying the current architecture
    # which is likely to be x86_64 - i.e. we will ignore any updates that only affect aarch64
    # for example.
    if test "$current_commit" == "$container_commit"; then
        echo "Generated container image for arch=$arch is up to date at commit $current_commit"
        continue
    fi

    buildah rmi "${imgtag}" &>/dev/null || true
    runv buildah manifest create "${imgtag}"

    # Download the ostree commit for each architecture, and turn them into container images,
    # then push to the registry
    for arch in "${ARCHES[@]}"; do
        ostree_ref=fedora:fedora/${ostree_version_component}/${arch}/${name}
        imgtag_arch=oci:${imgtag}-${arch}
        # To optimize local testing, set REPO_CACHE to a path to a repository which has
        # pre-pulled the ostree data.
        runv ostree --repo=repo pull "${REPO_CACHE:+-L ${REPO_CACHE}}" $ostree_ref
        rev=$(ostree --repo=repo rev-parse $ostree_ref)
        runv rpm-ostree compose container-encapsulate --repo repo $rev ${imgtag_arch}
        runv buildah manifest add --arch=$(arch_to_goarch ${arch}) "${imgtag}" ${imgtag_arch}
    done

    # Push to the primary target registry
    target=docker://${primary_imgtag}
    echo "Pushing to ${target}"
    runv buildah manifest push --all "${imgtag}" ${target}
    # If we have an alias, synchronize that
    if test -n "${aliased_name}"; then
        runv skopeo copy ${target} docker://${canonical_registry}/${aliased_name}
    fi
    # And handle secondary registries
    echo "Copying to secondary registries"
    for registry in "${secondary_registries[@]}"; do
        runv skopeo copy ${target} docker://${registry}/${imgname}
        if test -n "${aliased_name}"; then
            runv skopeo copy ${target} docker://${registry}/${aliased_name}
        fi
    done
    echo "done synchronizing ${name}"
    popd
    rm "${name}" -rf
done

echo "done"
