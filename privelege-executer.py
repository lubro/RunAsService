#!/usr/bin/env python3

# Parameters:
# launcher.py application, parameters, [:groups]

import subprocess
import os
import sys


def run():
    # Abort if insufficant ammount of parameters
    if len(sys.argv) < 3:
        return 1

    # Read and apply parameters
    application = sys.argv[1]
    parameters = sys.argv[2]

    if len(sys.argv) > 3:
        groups = [int(group) for group in sys.argv[3:]]
    else:
        groups = []

    # Drop privileges
    os.setgroups(groups)
    os.setgid(1000)
    os.setuid(1000)

    # Launch application
    subprocess.Popen(
            [application, parameters],
            stdin=None,
            stdout=None,
            stderr=None,
            close_fds=True)


if __name__ == '__main__':
    run()
