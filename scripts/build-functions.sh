# Copyright (C) 2012 Red Hat Inc.
# SPDX-License-Identifier:  GPL-2.0+
# Sourced by buildbranched and buildrawhide
set -x

function echogit() {
    echo "Using GIT revision: $(git log -n 1 --pretty="%h: %ci - %s")"
}

echogit

[ -n "$ARCH" ] && {
TREEPREFIX="/mnt/koji/tree"
EXPANDARCH="-$ARCH"
DEPOPTS="${DEPOPTS} --nomail"
MASHOPTS="-c /etc/mash/mash.$ARCH.conf"
TOMAIL="secondary@lists.fedoraproject.org $ARCH@lists.fedoraproject.org"
SUBJECT="${ARCH} ${SUBJECT}"
FROM="${ARCH} ${FROM}"
RSYNCPREFIX=""
}

# set the Mockconfig to use for composing, all arches except ppc/aarch64 run on x86 boxes
MOCKCONFIG="fedora-${DIST}-compose-i386"

[ "$ARCH" == "ppc" ] && {
MOCKCONFIG="fedora-${DIST}-compose-ppc64"

}

[ "$ARCH" == "arm" ] && {
MOCKCONFIG="fedora-${DIST}-compose-aarch64"

}

RSYNC_OPTS="-rlptDHhv --delay-updates"
DESTPATH="$TREEPREFIX/development/$BRANCHED/"

# basepath of $0
scriptname="${0##*/}"
[ -z "$DATE" ] && {
    echo "usage: ${scriptname} <date>"
    exit 1
}

TMPDIR=`mktemp -d /tmp/${DIST}.$DATE.XXXX`
logdir="/mnt/koji/mash/${DIST}-$DATE/logs"
mkdir -p "${logdir}"


echo "Compose started at $(date --utc)" > "$logdir/start"



logfile="${logdir}/build${DIST}.log"
touch "${logfile}"
function log()
{
    local message="${1}"
    echo "$(date --utc) build${DIST}: ${message}" | tee -a "${logfile}" >&2
}

fedmsg_json_start=$(printf '{"log": "start", "branch": "%s", "arch": "%s"}' "$BRANCHED" "$ARCH")
fedmsg_json_done=$(printf '{"log": "done", "branch": "%s", "arch": "%s"}' "$BRANCHED" "$ARCH")

FEDMSG_MODNAME="compose"
FEDMSG_CERTPREFIX="releng"
. ./scripts/fedmsg-functions.sh

log "started"
send_fedmsg "${fedmsg_json_start}" ${DIST} start

# Block pkgs only when running for primary
if [[ -z "${ARCH}" ]]; then
    log "blocking retired packages"
    if [ "$ENVIRONMENT" == "production" ]; then
        ./scripts/block_retired.py --profile compose_koji
    else
        ./scripts/block_retired.py  --staging
    fi
fi


log "git clone of comps started"
pushd $TMPDIR
git clone https://git.fedorahosted.org/git/comps.git && {
    pushd comps
    echogit
    make "${COMPSFILE}"
    cp "${COMPSFILE}" $logdir/
    popd
}
popd
log "git clone of comps finished"

[ -f "$logdir/${COMPSFILE}" ] || exit 1

log "mock init"
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --init
log "mock install base packages"
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --no-clean --install koji yum createrepo make intltool findutils mash yum-utils rsync repoview hardlink
if [[ "${DIST}" == "branched" ]]
then
    # until we move to bodhi lets not be strict about the gpg keys
    $MOCK -r $MOCKCONFIG --uniqueext=$DATE --chroot "sed -i -e 's|strict_keys = True|strict_keys = False|g' /etc/mash/${DIST}.mash"
    #disable delta close to release as we do not want them in the final trees
    $MOCK -r $MOCKCONFIG --uniqueext=$DATE --chroot "sed -i -e 's|delta = True|delta = False|g' /etc/mash/${DIST}.mash"
    # secondary arches are a bit harder to make sure everything is signed lets not be too strict, but actual release compsoes need to be.
    [ -n "$ARCH" ] && {
    $MOCK -r $MOCKCONFIG --uniqueext=$DATE --chroot "sed -i -e 's|strict_keys = True|strict_keys = False|g' /etc/mash/${DIST}.$ARCH.mash"
    }
fi
# Copy in the hosts file so that we get the right address for koji
log "mock setup /etc/hosts"
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --copyin /etc/hosts /etc/hosts >/dev/null 2>&1 # this reports to fail, but actually works

send_fedmsg "${fedmsg_json_start}" ${DIST} mash.start

log "starting mash"
# Drop privs here so that we run as the masher UID
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --chroot "chown mockbuild:mockbuild /var/cache/mash" || exit 1
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --unpriv --chroot "mash $MASHOPTS -p $TREEPREFIX/development/$BRANCHED -o ${MASHDIR} --compsfile $logdir/${COMPSFILE} $BRANCHED$EXPANDARCH > $logdir/mash.log 2>&1" || exit 1

send_fedmsg "${fedmsg_json_done}" ${DIST} mash.complete

log "finished mash"
log "starting hardlink"
# hardlink the noarch deltarpms between all arches
    $MOCK -r $MOCKCONFIG --uniqueext=$DATE --chroot "hardlink -v -c ${MASHDIR}/$BRANCHED$EXPANDARCH"
#    $MOCK -r $MOCKCONFIG --uniqueext=$DATE --chroot "hardlink -v -c ${MASHDIR}/$BRANCHED$EXPANDARCH/*/os/drpms/"
log "finished hardlink"

log "starting repodiff"
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --chroot "rm -f /var/lib/rpm/__db*"
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --unpriv --chroot "/usr/bin/repodiff -s -q --new=file://${MASHDIR}/$BRANCHED$EXPANDARCH/source/SRPMS --old=file://$TREEPREFIX/development/$BRANCHED/source/SRPMS > $logdir/repodiff"
log "finished repodiff"

log "starting spam-o-matic"
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --unpriv --chroot "/usr/share/mash/spam-o-matic $DEPOPTS ${MASHDIR}/$BRANCHED$EXPANDARCH >$logdir/depcheck"
log "finished spam-o-matic"

log "starting mock clean"
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --clean
log "finished mock clean"

[ -z "$ARCH" ] && {
log "starting atomic tree creation"
MOCKCONFIG="fedora-${DIST}-compose-x86_64"
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --init
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --install rpm-ostree git
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --shell "if [ ! -d $ATOMICREPO ]; then ostree init --repo=$ATOMICREPO --mode=archive-z2;fi"
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --shell "git clone https://git.fedorahosted.org/git/fedora-atomic.git $ATOMIC && pushd $ATOMIC && git log -n 1 --pretty='%h: %ci - %s' && git checkout ${GIT_BRANCH}"
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --shell "cd $ATOMIC && sed -i -e 's|mirrorlist=.*$|baseurl=http://kojipkgs.fedoraproject.org/mash/${DIST}/x86_64/os/|g' fedora*repo"
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --shell "rpm-ostree compose tree --repo=$ATOMICREPO $ATOMIC/fedora-atomic-docker-host.json >$logdir/atomic"
if [ "$BRANCHED" = "rawhide"]; then
    # We're only generatic static deltas for rawhide.
    REF="fedora-atomic/$BRANCHED/x86_64/docker-host"
    $MOCK -r $MOCKCONFIG --uniqueext=$DATE --shell "ostree --repo=$ATOMICREPO rev-parse ${REF} && ostree --repo=$ATOMICREPO static-delta generate ${REF}"
    # TODO: GPG sign it
fi
log "finished atomic tree creation"
}

send_fedmsg "${fedmsg_json_start}" ${DIST} pungify.start

log "starting critppath generation"
#only run critpath on primary arch
[ -z "$ARCH" ] && {
./scripts/critpath.py --url file:///mnt/koji/mash/$DIST-$DATE/$BRANCHED/ -o /mnt/koji/mash/$DIST-$DATE/logs/critpath.txt branched &> /mnt/koji/mash/$DIST-$DATE/logs/critpath.log
log "finished critppath generation"

log "starting pungify"
for basearch in armhfp i386 x86_64 ; do
    HOST=$(koji list-hosts --quiet --enabled --ready --arch=$basearch  --channel compose | sed 's|/| |g' | sort -g -k4 -k5r | awk -F ' ' '{ print $1 ; exit }')
    ./scripts/pungify $DATE $BRANCHED $basearch $HOST $DIST > $logdir/pungify-$basearch.log 2>&1 &
    done
}
wait
log "finished pungify"

send_fedmsg "${fedmsg_json_done}" ${DIST} pungify.complete

log "starting build_composeinfo"
echo "Running build_composeinfo"
./scripts/build_composeinfo --name Fedora-${BRANCHED}-${DATE} /mnt/koji/mash/$DIST-$DATE/$BRANCHED/

log "finished build_composeinfo"
log "starting mock clean"
$MOCK -r $MOCKCONFIG --uniqueext=$DATE --clean
log "finished mock clean"

[ -n "$NOSYNC" ] && exit $rc

log "started linking finished tree"
# Create a rawhide link in /mnt/koji/mash, deltas et al depend on this
rm /mnt/koji/mash/$DIST
ln -s /mnt/koji/mash/$DIST-$DATE/$BRANCHED$EXPANDARCH/ /mnt/koji/mash/$DIST
log "finished linking finished tree"

echo "Compose finished at $(date --utc)" >> $logdir/finish
echo >> $logdir/finish
log "finished compose"

send_fedmsg "${fedmsg_json_start}" ${DIST} rsync.start

log "started compose sync"
# data
$RSYNCPREFIX /usr/bin/rsync $RSYNC_OPTS $RSYNC_EXTRA_OPTS --exclude repodata/ ${MASHDIR}/$BRANCHED$EXPANDARCH/ $DESTPATH
# repodata & cleanup
$RSYNCPREFIX /usr/bin/rsync $RSYNC_OPTS $RSYNC_EXTRA_OPTS --delete --delete-after ${MASHDIR}/$BRANCHED$EXPANDARCH/ $DESTPATH
#rsync teh atomic tree
$RSYNCPREFIX /usr/bin/rsync $RSYNC_OPTS --delete --delete-after $ATOMICREPO $ATOMICDEST
log "finished compose sync"

if [ "$?" = "0" ]; then
   export mail=0
fi

send_fedmsg "${fedmsg_json_done}" ${DIST} rsync.complete

log "starting sending email report"
if [ "$mail" = "0" ]; then
    for tomail in "$(echo $TOMAIL)" ; do
        cat $logdir/start $logdir/depcheck $logdir/repodiff $logdir/finish | \
             mutt -e "set from=\"$FROM\"" -e 'set envelope_from=yes' -s "$SUBJECT" $tomail
    done
fi
log "finished sending email report"

[ -z "$ARCH" ] && {
send_fedmsg "${fedmsg_json_start}" ${DIST} image.start

log "started checking out spin-kickstarts"
pushd ../
git clone https://git.fedorahosted.org/git/spin-kickstarts.git
pushd spin-kickstarts
git checkout "${GIT_BRANCH}"
echogit
log "finished checking out spin-kickstarts"
log "started building live/arm/cloud images"
../releng/scripts/build-livecds $BRANCHED $DATE $BRANCHED
../releng/scripts/build-arm-images $BRANCHED $DATE $BRANCHED
../releng/scripts/build-cloud-images $BRANCHED $DATE $BRANCHED nightly
log "finished starting building live/arm/cloud images"
popd
popd

send_fedmsg "${fedmsg_json_done}" ${DIST} image.complete
}

for koji in arm ppc s390
do
  if [ "$koji" = "arm" ]; then
     arches=aarch64
  elif [ "$koji" = "ppc" ]; then
     arches=ppc64,ppc64le
  elif [ "$koji" = "s390" ]; then
     arches=s390,s390x
  fi
  scripts/srpm-excluded-arch.py -a $arches --path ${MASHDIR}/$BRANCHED$EXPANDARCH/source/SRPMS/\*/ >$logdir/excludearch-$koji.log
done

send_fedmsg "${fedmsg_json_done}" ${DIST} complete

exit 0
