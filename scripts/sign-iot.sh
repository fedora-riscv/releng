#!/bin/bash

COMPOSE_ID=$1
KEY=$2
 
for checksum in $(find /mnt/koji/compose/iot/$COMPOSE_ID/compose/ -name  "*CHECKSUM")
do
    if grep -q BEGIN $checksum; then
        echo "$checksum is already signed"
    else
        cat $checksum >/tmp/sum && NSS_HASH_ALG_SUPPORT=+MD5 sigul sign-text -o /tmp/signed $KEY /tmp/sum && chmod 644 /tmp/signed && sudo mv /tmp/signed $checksum
    fi
done
