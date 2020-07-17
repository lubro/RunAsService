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


GROUP_RANGE = (1200, 100)


def setup(pipes, target_ids):
    os.close(pipes[0][1])
    os.close(pipes[1][0])

    select.select([pipes[0][0]], [], [])
    data = json.load(os.fdopen(pipes[0][0]))
    child_pid = str(data['child-pid'])

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

    with open('tmp.txt', 'w') as f:
        f.write(str([
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
            ])
            )

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

    os.write(pipes[1][1], b'1')


def launch(pipes, application, parameter):
    os.close(pipes[0][0])
    os.close(pipes[1][1])

    # Fix for ubuntu with older python/arch with newer
    if sys.version_info >= (3, 4):
        os.set_inheritable(pipes[0][1], True)
        os.set_inheritable(pipes[1][0], True)

    homedir = os.path.expanduser('~')

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
    with open('applications-conf.json', 'r') as f:
        mapping = json.load(f)

    try:
        user = mapping['users'][f'{uid}']
    except Exception:
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
        except Exception:
            print("False")
            return 1

        print(f'{application} {parameter}')

        # run bwrap

        info_pipe = os.pipe()
        blockns_pipe = os.pipe()

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
