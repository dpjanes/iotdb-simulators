#
#   website_home_1.py
#
#   David Janes
#   IOTDB
#   2013-12-11
#
#   Simulate a stove with four burners and an oven
#

import thing

from stove_1 import Stove
from light_1 import Thing as Light
from blinds_1 import Thing as Blinds
from rgb_2 import Thing as RGBLight

class Home1(thing.Thing):
    stated = {
        "kitchen" : {
            "stove" : Stove(),
            "light" : Light(),
        },
        "basement" : {
            "hue" : {
                "1" : RGBLight(),
                "2" : RGBLight(),
                "3" : RGBLight(),
            },
        },
        "bedroom" : {
            "light" : Light(),
            "blinds" : Blinds(),
        },
    }

## Epxorts
Thing = Home1
