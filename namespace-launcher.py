#!/usr/bin/env python3

import subprocess
import os
import json
import select
import grp
import pwd
import sys

from gi.repository import GLib
from pydbus import SessionBus
from pydbus.generic import signal


# This range might be similar to the one specified in /etc/subuid.
# The fix uid range here is for demo purpose only, in a real
# world implementation, this has to be replaced.
GROUP_RANGE = (1200, 100)


def setup(pipes, target_ids):
    # Close the pipes
    os.close(pipes[0][1])
    os.close(pipes[1][0])

    # Read from the info pipe
    select.select([pipes[0][0]], [], [])
    data = json.load(os.fdopen(pipes[0][0]))
    child_pid = str(data['child-pid'])

    # setup the new uidmapping
    subprocess.call([
        'newuidmap',
        child_pid,
        '0',
        str(os.getuid()),
        '1',
        str(os.getuid()),
        str(target_ids[0]),
        '1',
        ]
    )

    # setup the new gidmapping
    subprocess.call([
        'newgidmap',
        child_pid,
        '0',
        str(os.getgid()),
        '1',
        '1000',
        str(target_ids[1]),
        '1',
        str(GROUP_RANGE[0]),
        str(GROUP_RANGE[0]),
        str(GROUP_RANGE[1]),
        ]
    )

    # Write to and close the blocking pipe
    os.write(pipes[1][1], b'1')


def launch(pipes, application, parameter):
    # Close not required pipe ends
    os.close(pipes[0][0])
    os.close(pipes[1][1])

    # Fix for ubuntu with older python/arch with newer
    if sys.version_info >= (3, 4):
        os.set_inheritable(pipes[0][1], True)
        os.set_inheritable(pipes[1][0], True)

    # Expand the homedir
    homedir = os.path.expanduser('~')

    # Specifiy how bubblewrap is started:
    # --bind bindmounts the root directory
    # --unshare-user unshares a user namespace
    # --cap-add adds capabilities to process in namespace with uid 0
    # --uid run the process with the uid 0(inside the ns)
    # --userns-block-fd a pipe which blocks the execution
    # --info-fd a info pipe which provides infos like name
    args = ['bwrap',
            'bwrap',
            '--bind', '/', '/',
            '--bind', 'pulse', '{homedir}/.pulse',
            '--unshare-user',
            '--cap-add', 'CAP_SETGID',
            '--cap-add', 'CAP_SETUID',
            '--uid', '0',
            '--userns-block-fd', '%i' % pipes[1][0],
            '--info-fd', '%i' % pipes[0][1],
            './privelege-executer.py', application]

    # Extend target application parameters to the arguments
    args.extend(parameter)

    # Execute with path variable
    os.execlp(*args)


def run(application, parameter, uid):
    # Read the configuration for verification
    with open('applications-conf.json', 'r') as f:
        mapping = json.load(f)

    try:
        user = mapping['users'][f'{uid}']
    except KeyError:
        return 1
    print("validating")
    # Validate if user is allowed to launch the process
    if len(user['launch']) == 0 or (
            application not in user['launch']
            and user['launch'][0] != '*'):
        return 1

    if application in mapping['applications'].keys():
        uid = mapping['applications'][application]['uid']
        try:
            user_groups = mapping['users'][f'{uid}']['groups']
            user_gid = mapping['users'][f'{uid}']['group']
        except KeyError:
            print("False")
            return 1

        print(f'{application} {parameter}')

        # Open the pipes
        info_pipe = os.pipe()
        blockns_pipe = os.pipe()

        # For the process
        # running as two processes from here
        pid = os.fork()

        parameter = [parameter]
        parameter.extend([str(gid) for gid in user_groups])
        if pid == 0:
            launch([info_pipe, blockns_pipe], application, parameter)
        else:
            setup([info_pipe, blockns_pipe], [uid, user_gid])

    return 0


if __name__ == '__main__':
    args = sys.argv
    run(args[1], args[2], args[3])
