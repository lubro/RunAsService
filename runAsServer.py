#!/usr/bin/env python

import subprocess
import os
import json
import grp
import pwd

from gi.repository import GLib
from pydbus import SessionBus
from pydbus.generic import signal


class RunAs():
    """
    <node>
        <interface name="org.freedesktop.RunAs">
            <method name="Run">
                <arg direction="in" type="s" name="application"/>
                <arg direction="in" type="s" name="param"/>
            </method>
        </interface>
    </node>
    """

    def Run(self, application, parameter, dbus_context):
        print(f'{application} {parameter}')
        print(f'{dbus_context.sender}')
        with open('applications-conf.json', 'r') as f:
            mapping = json.load(f)

        bus = SessionBus()
        get_uid = bus.get('.DBus')
        uid = get_uid.GetConnectionUnixUser(dbus_context.sender)
        subprocess.Popen([
            './namespace-launcher.py',
            application, parameter,
            f'{uid}'])


if __name__ == '__main__':
    bus = SessionBus()
    bus.publish("org.freedesktop.RunAs", RunAs())
    loop = GLib.MainLoop()
    loop.run()
