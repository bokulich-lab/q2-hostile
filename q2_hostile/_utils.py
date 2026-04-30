# flake8: noqa
# ----------------------------------------------------------------------------
# Copyright (c) 2026, Bokulich Lab.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import subprocess


def run_command(cmd, verbose=True, **kwargs):
    if verbose:
        print(
            "Running external command line application(s). This may print "
            "messages to stdout and/or stderr."
        )
        print(
            "The command(s) being run are below. These commands cannot be "
            "manually re-run as they will depend on temporary files that no "
            "longer exist."
        )
        print()
        print("Command:", " ".join(cmd))
        print()

    return subprocess.run(cmd, check=True, **kwargs)
