#!/usr/bin/python
# clean up eol signed rpm
# Copyright (C) 2013 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0
"""Remove signed rpms after a release is end-of-life
"""

from __future__ import print_function
import os

KEYS = [
    '069C8460', '30C9ECF8',
    '4F2A6FD2', '897DA07A',
    '1AC70CE6', '6DF2196F',
    'DF9B0AE9', '0B86274E',
    '4EBFC273', 'D22E77F2',
    '57BBCCBA', 'E8E40FDE',
    '97A1071F', '069C8460',
    '10d90a9e', 'a82ba4b7',
    'f8df67e6', '1aca3465',
    'de7f38bd', 'a4d647e9',
    'fb4b18e6', 'ba094068',
    '246110c1', 'efe550f5',
    '95a43f54', 'a0a7badb',
    '8e1431d5', 'a29cb19c',
    '873529b8', '34ec9cba',
    '030d5aed', '81b46521',
    'e372e838', 'fdb19c98',
    '3b921d09', '64dab85d',
    'f5282ee4', '9db62fb1',
    '429476b4',
]

PREFIX = 'data/signed'

ROOT_PATH = '/mnt/koji/packages'


for root, dirs, files in os.walk(ROOT_PATH, topdown=False):
    for name in files:
        filepath = os.path.join(root, name)
        for key in KEYS:
            if os.path.join(PREFIX, str.lower(key)) in filepath:
                print(filepath)
                if os.path.exists(filepath):
                    os.remove(filepath)
                continue
    for name in dirs:
        filepath = os.path.join(root, name)
        for key in KEYS:
            if os.path.join(PREFIX, str.lower(key)) in filepath:
                print(filepath)
                if os.path.exists(filepath):
                    os.rmdir(filepath)
                continue
