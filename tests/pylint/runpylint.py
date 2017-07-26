#!/usr/bin/python3
# SPDX-License-Identifier:    GPL-2.0+
# Authors:
#     Robert Marshall <rmarshall@redhat.com>

import sys

from pocketlint import FalsePositive, PocketLintConfig, PocketLinter


class FedoraRelengLintConfig(PocketLintConfig):

    def __init__(self):
        PocketLintConfig.__init__(self)

    @property
    def disabledOptions(self):
        return ["W0105",           # String statement has no effect
                "W0110",           # map/filter on lambda could be replaced by comprehension
                "W0141",           # Used builtin function %r
                "W0142",           # Used * or ** magic
                "W0212",           # Access to a protected member of a client class
                "W0511",           # Used when a warning note as FIXME or XXX is detected.
                "W0603",           # Using the global statement
                "W0614",           # Unused import %s from wildcard import
                "I0011",           # Locally disabling %s
                ]

    @property
    def ignoreNames(self):
        return {}

if __name__ == "__main__":
    conf = FedoraRelengLintConfig()
    linter = PocketLinter(conf)
    rc = linter.run()
    sys.exit(rc)
