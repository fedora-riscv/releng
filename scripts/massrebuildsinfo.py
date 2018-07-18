#!/usr/bin/python -tt
# vim: fileencoding=utf8


PKG_SKIP_LIST = [
    'fedora-modular-release',
    'fedora-modular-repos',
    'fedora-release',
    'fedora-repos',
    'generic-release',
    'glibc32'
    'grub2',
    'kernel',
    'linux-firmware',
    'openh264',
    'redhat-rpm-config',
    'shim',
    'shim-signed',
    'shim-unsigned-aarch64',
    'shim-unsigned-x64',
]

MASSREBUILDS = {
    "f29":
    {
        "buildtag": 'f29-rebuild',  # tag to build from
        "epoch": '2018-07-12 17:00:00.000000',  # rebuild anything not built after this date
        "targets": ['f29-candidate', 'rawhide', 'f29'],  # build targets to check for existing builds to skip rebuild
        "target": 'f29-rebuild',  # target to build into
        "desttag": 'f29',  # Tag where fixed builds go
        "product": "Fedora",  # for BZ product field
        "version": "rawhide",  # for BZ version field
        "tracking_bug": 1602938,  # Tracking bug for mass build failures
        "wikipage": "https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild",
        "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
    },
    "f28":
    {
        "buildtag": 'f28-rebuild',  # tag to build from
        "epoch": '2018-02-06 01:20:06.000000',  # rebuild anything not built after this date
        "targets": ['f28-candidate', 'rawhide', 'f28'],  # build targets to check for existing builds to skip rebuild
        "target": 'f28-rebuild',  # target to build into
        "desttag": 'f28',  # Tag where fixed builds go
        "product": "Fedora",  # for BZ product field
        "version": "28",  # for BZ version field
        "tracking_bug": 1555378,  # Tracking bug for mass build failures
        "wikipage": "https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild",
        "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
    },
    "f27":
    {
        "epoch": '2017-07-31 11:20:00.000000',
    }
}
