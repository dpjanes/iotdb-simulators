#
#   stove_1.py
#
#   David Janes
#   IOTDB
#   2013-12-11
#
#   Simulate a stove with four burners and an oven
#

import thing

class Light(thing.Thing):
    stated = {
        "on" : False,
    }

class Burner(thing.Thing):
    stated = {
        "on" : False,
        "intensity" : 0,
    }
    validated = {
        "intensity" : ( thing.validate_ranged, 0, 10, ),
    }

class Oven(thing.Thing):
    stated = {
        "on" : False,
        "temperature" : 0,
        "light" : Light(),
    }
    validated = {
        "temperature" : ( thing.validate_ranged, 0, 500, ),
    }

class Stove(thing.Thing):
    port = 9131

    stated = {
        "burner" : {
            "1" : Burner(),
            "2" : Burner(),
            "3" : Burner(),
            "4" : Burner(),
        },
        "oven" : Oven(),
        "light" : Light(),
    }

## primary export
Thing = Stove
