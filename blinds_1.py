#
#   blinds_1.py
#
#   David Janes
#   IOTDB
#   2013-12-17
#
#   Blinds
#

import sys
import json

import bottle

import iotdb_log
import thing

class Thing(thing.Thing):
    port = 9161
    stated = {
        "open" : True
    }
