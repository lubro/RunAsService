#!/usr/bin/env python

import subprocess
import os
import json
import grp
import pwd

from gi.repository import GLib
from pydbus import SessionBus
from pydbus.generic import signal


# A class providing a D-Bus interface
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
        # Print applicationname, parameters and dbus origin address for debugging
        print(f'{application} {parameter}')
        print(f'{dbus_context.sender}')

        # Open and read the configuration file
        with open('applications-conf.json', 'r') as f:
            mapping = json.load(f)

        # Use to the D-bus to get the uid of the client, sending this message
        bus = SessionBus()
        get_uid = bus.get('.DBus')
        uid = get_uid.GetConnectionUnixUser(dbus_context.sender)

        # Call the namespace launcher
        subprocess.Popen([
            './namespace-launcher.py',
            application, parameter,
            f'{uid}'])


if __name__ == '__main__':
    bus = SessionBus()
    bus.publish("org.freedesktop.RunAs", RunAs())
    loop = GLib.MainLoop()
    loop.run()
