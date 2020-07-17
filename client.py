import sys

from pydbus import SessionBus

bus = SessionBus()
notifications = bus.get('.RunAs')

parameter = ''
if len(sys.argv) > 2:
    for item in sys.argv[2:]:
        parameter = f'{parameter} {item}'
print(notifications.Run(sys.argv[1], parameter))
