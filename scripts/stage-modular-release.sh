#!/bin/bash
# Copyright (C) 2016 Red Hat Inc.
# SPDX-License-Identifier:  GPL-2.0+


RELEASEVER=$1
COMPOSEID=$2
STAGE=$3
KEY=$4

DESTDIR="/pub/alt/unofficial/releases/"

SHORTRELEASEVER=$(echo $RELEASEVER | sed -e 's|_.*||g')

BASE="/mnt/koji/compose/"

for checksum in $(find $BASE/$SHORTRELEASEVER/$COMPOSEID/compose/ -name  *CHECKSUM)
do 
  cat $checksum >/tmp/sum && NSS_HASH_ALG_SUPPORT=+MD5 sigul sign-text -o /tmp/signed $KEY /tmp/sum && chmod 644 /tmp/signed && sudo mv /tmp/signed $checksum
done

sudo -u ftpsync mkdir -p $DESTDIR/$RELEASEVER/
sudo -u ftpsync chmod 700 $DESTDIR/$RELEASEVER

sudo -u ftpsync compose-partial-copy --arch=armhfp --arch=x86_64 --arch src --arch=aarch64 --arch=i386 --arch=ppc64 --arch=ppc64le \
     $BASE/$SHORTRELEASEVER/$COMPOSEID/compose/$dir/ $DESTDIR/$RELEASEVER/$dir/ \
     --variant Server 


sudo -u ftpsync chmod 755 $DESTDIR/$RELEASEVER/

sudo -u ftpsync du -hs $DESTDIR/$RELEASEVER/
