#
#   rgb_1.py
#
#   David Janes
#   IOTDB
#   2013-12-09
#
#   Simulate a light that has RGB controls
#

import sys
import json

import bottle

import iotdb_log
import thing

class Thing(thing.Thing):
    port = 9131
    stated = {
        "on" : True,
        "red" : 1.0,
        "green" : 1.0,
        "blue" : 1.0,
    }
    validated = {
        "red" : ( thing.validate_ranged, 0.0, 1.0, ),
        "green" : ( thing.validate_ranged, 0.0, 1.0, ),
        "blue" : ( thing.validate_ranged, 0.0, 1.0, ),
    }
