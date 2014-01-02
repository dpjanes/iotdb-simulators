# Simulators

## To run a simulator
### On it's assigned port

    python serve.py dimmer_1

The assigned port is specified in the class

### On a chosen port

    python serve.py --port 8080 dimmer_1

### On a random port with Bonjour

    python serve.py --bonjour dimmer_1

The port is printed to stdout. 
The bonjour name is "dimmer_1._json._tcp.local."_

## To get data from / change data on a simulator

Command line utility. Call 'node put' with the URL and the X=Y arguments.
We try to do the 'right thing' with Y, i.e. convert numbers to numbers,
bools to bools. The simulators are pretty good with value coercion also.

    node put http://localhost:8080/ on=true
    node put http://localhost:8080/ on=1
    node put http://localhost:8080/ on=0
    node put http://localhost:8080/ "rgb=#FF0000"

This can also be done by the name of the server

    node put light_1 on=true
    node put light_1 on=1
    node put dimmer_1 on=true brightness=0.4
    node put rgb_1 "rgb=#FF0000"
