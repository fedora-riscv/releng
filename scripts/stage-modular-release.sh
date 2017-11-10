#!/bin/bash
# Copyright (C) 2016 Red Hat Inc.
# SPDX-License-Identifier:  GPL-2.0+


RELEASEVER=$1
COMPOSEID=$2
STAGE=$3
KEY=$4
PRERELEASE=$5

DESTDIR="/pub/fedora/linux/modular/releases/"

SHORTRELEASEVER=$(echo $RELEASEVER | sed -e 's|_.*||g')

if [ $PRERELEASE == 1 ]; then
  RELPREFIX="test/"
else
  RELPREFIX=""
fi

BASE="/mnt/koji/compose/"

for checksum in $(find $BASE/$SHORTRELEASEVER/$COMPOSEID/compose/ -name  *CHECKSUM)
do
  if grep -q BEGIN $checksum; then
    echo "$checksum is already signed"
  else	
    cat $checksum >/tmp/sum && NSS_HASH_ALG_SUPPORT=+MD5 sigul sign-text -o /tmp/signed $KEY /tmp/sum && chmod 644 /tmp/signed && sudo mv /tmp/signed $checksum
  fi
done

sudo -u ftpsync mkdir -p $DESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync chmod 700 $DESTDIR/$RELPREFIX$RELEASEVER

sudo -u ftpsync compose-partial-copy --arch=armhfp --arch=x86_64 --arch src --arch=aarch64 --arch=i386 --arch=ppc64 --arch=ppc64le \
     $BASE/$SHORTRELEASEVER/$COMPOSEID/compose/$dir/ $DESTDIR/$RELPREFIX$RELEASEVER/$dir/ \
     --variant Server

sudo -u ftpsync scripts/build_composeinfo $DESTDIR/$RELPREFIX$RELEASEVER/
sudo scripts/build_composeinfo $BASE/$SHORTRELEASEVER/$COMPOSEID/compose/


sudo -u ftpsync chmod 750 $DESTDIR/$RELPREFIX$RELEASEVER/

sudo -u ftpsync du -hs $DESTDIR/$RELPREFIX$RELEASEVER/
