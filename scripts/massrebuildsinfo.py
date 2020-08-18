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


# keep this sorted new -> old
MASSREBUILDS = {
    #f34 ftbfs bug tracker: TBA
    "f33":
        {
            "buildtag": 'f33-rebuild',  # tag to build from
            "epoch": '2020-07-27 10:00:00.000000',  # rebuild anything not built after this date
            "module_mass_rebuild_epoch": '2020-07-27T10:00:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_branching_epoch": '2020-08-11T12:30:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_rebuild_platform": "f33",
            # rebuild all modules that has build time dependency on this platform, this is used during mass rebuild time
            "module_mass_branching_platform": "f34",
            # rebuild all modules that has run time dependency on this platform, this is used during mass branching time
            "targets": ['f33-candidate', 'rawhide', 'f33'],
            # build targets to check for existing builds to skip rebuild
            "target": 'f33-rebuild',  # target to build into
            "desttag": 'f33',  # Tag where fixed builds go
            "product": "Fedora",  # for BZ product field
            "version": "rawhide",  # for BZ version field, rawhide before branching or xx after branching
            "rawhide_version": "33",  # for next version calculation and other comments
            "tracking_bug": "1803234",  # Tracking bug for mass build failures
            "wikipage": "https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild",
            "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
        },
    "f32":
    {
        "buildtag": 'f32-rebuild',  # tag to build from
        "epoch": '2020-01-28 03:30:00.000000',  # rebuild anything not built after this date
        "module_mass_rebuild_epoch": '2020-01-28T03:30:00Z',  # rebuild anything not built after this date for modules
        "module_mass_branching_epoch": '2020-02-11T23:30:00Z',  # rebuild anything not built after this date for modules
        "module_mass_rebuild_platform": "f32",  # rebuild all modules that has build time dependency on this platform, this is used during mass rebuild time
        "module_mass_branching_platform": "f33",  # rebuild all modules that has run time dependency on this platform, this is used during mass branching time
        "targets": ['f32-candidate', 'rawhide', 'f32'],  # build targets to check for existing builds to skip rebuild
        "target": 'f32-rebuild',  # target to build into
        "desttag": 'f32',  # Tag where fixed builds go
        "product": "Fedora",  # for BZ product field
        "version": "rawhide",  # for BZ version field, rawhide before branching or xx after branching
        "rawhide_version": "32",  # for next version calculation and other comments
        "tracking_bug": "1750908",  # Tracking bug for mass build failures
        "wikipage": "https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild",
        "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
    },
    "f31":
    {
        "buildtag": 'f31-rebuild',  # tag to build from
        "epoch": '2019-07-24 09:40:00.000000',  # rebuild anything not built after this date
        "module_mass_rebuild_epoch": '2019-07-24T09:40:00Z',  # rebuild anything not built after this date for modules
        "module_mass_branching_epoch": '2019-08-13T17:00:00Z',  # rebuild anything not built after this date for modules
        "module_mass_rebuild_platform": "f31",  # rebuild all modules that has build time dependency on this platform, this is used during mass rebuild time
        "module_mass_branching_platform": "f32",  # rebuild all modules that has run time dependency on this platform, this is used during mass branching time
        "targets": ['f31-candidate', 'rawhide', 'f31'],  # build targets to check for existing builds to skip rebuild
        "target": 'f31-rebuild',  # target to build into
        "desttag": 'f31',  # Tag where fixed builds go
        "product": "Fedora",  # for BZ product field
        "version": "rawhide",  # for BZ version field, rawhide before branching or xx after branching
        "rawhide_version": "31",  # for next version calculation and other comments
        "tracking_bug": "1700317",  # Tracking bug for mass build failures
        "wikipage": "https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild",
        "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
    },
    "f30":
    {
        "buildtag": 'f30-rebuild',  # tag to build from
        "epoch": '2019-01-31 10:10:00.000000',  # rebuild anything not built after this date
        "module_mass_rebuild_epoch": '2019-02-13T18:30:00Z',  # rebuild anything not built after this date for modules
        "module_mass_branching_epoch": '2019-03-04T18:00:00Z',  # rebuild anything not built after this date for modules
        "module_mass_rebuild_platform": "f30",  # rebuild all modules that has build time dependency on this platform, this is used during mass rebuild time
        "module_mass_branching_platform": "f31",  # rebuild all modules that has run time dependency on this platform, this is used during mass branching time
        "targets": ['f30-candidate', 'rawhide', 'f30'],  # build targets to check for existing builds to skip rebuild
        "target": 'f30-rebuild',  # target to build into
        "desttag": 'f30',  # Tag where fixed builds go
        "product": "Fedora",  # for BZ product field
        "version": "rawhide",  # for BZ version field, rawhide before branching or xx after branching
        "rawhide_version": "30",  # for next version calculation and other comments
        "tracking_bug": "1674516",  # Tracking bug for mass build failures
        "wikipage": "https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild",
        "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
    },
    "f29":
    {
        "buildtag": 'f29-rebuild',  # tag to build from
        "epoch": '2018-07-12 17:00:00.000000',  # rebuild anything not built after this date
        "targets": ['f29-candidate', 'rawhide', 'f29'],  # build targets to check for existing builds to skip rebuild
        "target": 'f29-rebuild',  # target to build into
        "desttag": 'f29',  # Tag where fixed builds go
        "product": "Fedora",  # for BZ product field
        "version": "29",  # for BZ version field
        "tracking_bug": 1602938,  # Tracking bug for mass build failures
        "wikipage": "https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild",
        "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
        "current_rawhide": "29",
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
