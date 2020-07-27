#!/usr/bin/python3
import sys
from pydbus import SessionBus

# Getthe D-Bus connection to the RunAsService
bus = SessionBus()
run_as_service = bus.get('.RunAs')

# Parse commandline parameters.
# The first is the name of the application to start.
# All others are forwarded as parameters for the application.

# No additional parameters by default
parameter = ''
# Parse if there are additional parameters
if len(sys.argv) > 2:
    for item in sys.argv[2:]:
        parameter = f'{parameter} {item}'

# Print the value, returned by the RunAsService
print(run_as_service.Run(sys.argv[1], parameter))
