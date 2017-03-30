#!/bin/bash
# Copyright (C) 2016 Red Hat Inc.
# SPDX-License-Identifier:  GPL-2.0+


RELEASEVER=$1
COMPOSEID=$2
STAGE=$3
KEY=$4
PRERELEASE=$5

DESTDIR="/pub/fedora/linux/releases/"
ALTDESTDIR="/pub/alt/releases/"
STAGEDIR="/pub/alt/stage/"

ALTARCHDESTDIR="/pub/fedora-secondary/releases/"

SHORTRELEASEVER=$(echo $RELEASEVER | sed -e 's|_.*||g')

if [ $PRERELEASE == 1 ]; then
  RELPREFIX="test/"
else
  RELPREFIX=""
fi

BASE="/mnt/koji/compose/"

for checksum in $(find $BASE/$SHORTRELEASEVER/$COMPOSEID/compose/ -name  *CHECKSUM)
do 
  cat $checksum >/tmp/sum && NSS_HASH_ALG_SUPPORT=+MD5 sigul sign-text -o /tmp/signed $KEY /tmp/sum && chmod 644 /tmp/signed && sudo mv /tmp/signed $checksum
done

sudo -u ftpsync mkdir -p $DESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync chmod 700 $DESTDIR/$RELPREFIX$RELEASEVER
sudo -u ftpsync mkdir -p $ALTDESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync chmod 700 $ALTDESTDIR/$RELPREFIX$RELEASEVER
sudo -u ftpsync mkdir -p $ALTARCHDESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync chmod 700 $ALTARCHDESTDIR/$RELPREFIX$RELEASEVER

sudo -u ftpsync compose-partial-copy --arch=armhfp --arch=x86_64 --arch src \
     $BASE/$SHORTRELEASEVER/$COMPOSEID/compose/$dir/ $DESTDIR/$RELPREFIX$RELEASEVER/$dir/ \
     --variant Everything --variant CloudImages --variant Docker --variant Server --variant Spins --variant Workstation \
     --link-dest=/pub/fedora/linux/development/$SHORTRELEASEVER/Everything/ --link-dest=$STAGEDIR/$STAGE/Everything/ --link-dest=$STAGEDIR/$STAGE/$dir/

sudo -u ftpsync compose-partial-copy --arch=armhfp --arch=x86_64 --arch src \
     $BASE/$SHORTRELEASEVER/$COMPOSEID/compose/$dir/ $ALTDESTDIR/$RELPREFIX$RELEASEVER/$dir/ \
     --variant Cloud --variant Labs \
     --link-dest=/pub/fedora/linux/development/$SHORTRELEASEVER/Everything/ --link-dest=$STAGEDIR/$STAGE/Everything/ --link-dest=$STAGEDIR/$STAGE/$dir/


sudo -u ftpsync compose-partial-copy --arch=aarch64 --arch=i386 --arch=ppc64 --arch=ppc64le \
     $BASE/$SHORTRELEASEVER/$COMPOSEID/compose/$dir /$ALTARCHDESTDIR/$RELPREFIX$RELEASEVER/$dir/ \
     --exclude=s390x \
     --variant Everything --variant Cloud --variant CloudImages --variant Docker --variant Labs --variant Server --variant Spins --variant Workstation \
     --link-dest=/pub/fedora/linux/development/$SHORTRELEASEVER/Everything/ --link-dest=$STAGEDIR/$STAGE/Everything/ --link-dest=$STAGEDIR/$STAGE/$dir/

sudo -u ftpsync scripts/build_composeinfo $DESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync scripts/build_composeinfo $ALTDESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync scripts/build_composeinfo $ALTARCHALTDESTDIR/$RELPREFIX$RELEASEVER/
sudo scripts/build_composeinfo $BASE$RELEASEVER/$COMPOSEID/compose/

sudo -u ftpsync chmod 750 $DESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync chmod 750 $ALTDESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync chmod 750 $ALTARCHALTDESTDIR/$RELPREFIX$RELEASEVER/

sudo -u ftpsync du -hs $DESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync du -hs $ALTDESTDIR/$RELPREFIX$RELEASEVER/
sudo -u ftpsync du -hs $ALTARCHALTDESTDIR/$RELPREFIX$RELEASEVER/
