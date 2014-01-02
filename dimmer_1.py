#
#   dimmer_1.py
#
#   David Janes
#   IOTDB
#   2013-12-09
#
#   Simulate a single light that can be turned on or off
#

import sys
import json

import bottle

import iotdb_log
import thing

class Thing(thing.Thing):
    port = 9111
    stated = {
        "on" : True,
        "brightness" : 1.0,
    }
    validated = {
        "brightness" : ( thing.validate_ranged, 0.0, 1.0, ),
    }
