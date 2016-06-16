#!/bin/bash
# Copyright (C) 2016 Red Hat Inc.
# SPDX-License-Identifier:  GPL-2.0+


VELEASEVER=$1
COMPOSEID=$2
STAGE=$3
KEY=$4
PRERELEASE=$5
ARCH=$6

DESTDIR="/pub/fedora/linux/releases/"
ALTDESTDIR="/pub/alt/releases/"
STAGEDIR="/pub/alt/stage/"

[ -n "$ARCH" ] && {
DESTDIR="/pub/fedora-secondary/releases/"
ALTDESTDIR="/pub/fedora-secondary/releases/"
STAGEDIR="/pub/alt/stage/"
}

if $PRERELEASE == 1
then
  RELPREFIX="test/"
else
  RELPREFIX=""

BASE="/mnt/koji/compose/"

echo "Enter the password for the releasekey"
read pass

for checksum in $(find $BASE/$RELEASEVER/$COMPOSEID/compose/ -name  *CHECKSUM); 
do 
  cat $checksum >/tmp/sum && NSS_HASH_ALG_SUPPORT=+MD5 sigul --batch sign-text -o /tmp/signed $KEY /tmp/sum $pass && chmod 644 /tmp/signed && sudo mv /tmp/signed $checksum
done

sudo -u ftpsync mkdir -p $DESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync chmod 700 $DESTDIR/$RELPREFIX$RELEASEVER
sudo -u ftpsync mkdir -p $ALTDESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync chmod 700 $ALTDESTDIR/$RELPREFIX$RELEASEVER

for dir in Everything CloudImages  Docker Server  Spins  Workstation
do 
  sudo -u ftpsync rsync -avhH $BASE/$RELEASEVER/$COMPOSEID/compose/$dir/ $DESTDIR/$RELPREFIX$RELEASEVER/$dir/ --link-dest=/pub/fedora/linux/development/$RELEASEVER/Everything/ --link-dest=$STAGEDIR/$STAGE/Everything/ --link-dest=$STAGEDIR/$STAGE/$dir/
done

for dir in Cloud Labs ; do sudo -u ftpsync rsync -avhH $BASE/$RELEASEVER/$COMPOSEID/compose/$dir/ $ALTDESTDIR/$RELPREFIX$RELEASEVER/$dir/ --link-dest=/pub/fedora/linux/development/$RELEASEVER/Everything/ --link-dest=$STAGEDIR/$STAGE/Everything/ --link-dest=$STAGEDIR/$STAGE/$dir/; done

sudo -u ftpsync scripts/build_composeinfo $DESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync scripts/build_composeinfo $ALTDESTDIR/$RELPREFIX$RELEASEVER/

sudo -u ftpsync chmod 750 $DESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync chmod 750 $ALTDESTDIR/$RELPREFIX$RELEASEVER/

sudo -u ftpsync du -hs $DESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync du -hs $ALTDESTDIR/$RELPREFIX$RELEASEVER/

