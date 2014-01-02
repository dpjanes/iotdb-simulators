#
#   rgb_2.py
#
#   David Janes
#   IOTDB
#   2013-12-09
#
#   Simulate a light that has RGB controls
#   This version uses #FFFFFF hex style
#

import sys
import json
import re

import bottle

import iotdb_log
import thing

class Thing(thing.Thing):
    port = 9141
    stated = {
        "on" : True,
        "rgb" : "#FF0000",
    }
    validated = {
        "rgb" : ( thing.validate_rgb, ),
    }
