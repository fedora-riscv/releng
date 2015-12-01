#!/bin/bash

# Copyright (C) 2015 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0

git clone https://pagure.io/releng.git /tmp/releng
pushd /tmp/releng/docs
make html
popd

git clone ssh://git@pagure.io/docs/releng.git /tmp/releng-doc
cd /tmp/releng-doc
git rm -fr ./*
cp -r /tmp/releng/docs/build/html/* ./
git add .
git commit -s -m "update rendered releng docs"
git push origin master


rm -rf  /tmp/releng/ /tmp/releng-doc/
