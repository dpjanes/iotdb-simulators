#
#   serve.py
#
#   David Janes
#   IOTDB
#   2013-12-09
#
#   Run servers
#

import sys
import json
import md5
import os.path
import imp
import traceback

from optparse import OptionParser

import bottle

import iotdb_log
import thing

MIME_JSON = "application/json"
MIME_TEXT = "text/plain"
MIME_HTML = "text/html"

#
#   Command line arguments
#
parser = OptionParser()
parser.add_option(
    "", "--bonjour",
    default = False,
    action = "store_true",
    dest = "bonjour",
    help = "Run as a bonjour server (rather than at fixed port)",
)
parser.add_option(
    "", "--flup",
    default = False,
    action = "store_true",
    dest = "flup",
    help = "Run as a flup server (use --port too)",
)
parser.add_option(
    "", "--pidfile",
    dest = "pidfile",
    help = "Write the PID of this process to this file",
    default = None,
)
parser.add_option(
    "", "--port",
    dest = "port",
    help = "Port to run server on",
    default = None,
)
parser.add_option(
    "", "--host",
    dest = "host",
    help = "Host to tun server on (default: 0.0.0.0)",
    default = "0.0.0.0",
)
parser.add_option(
    "", "--mqtt-host",
    dest = "mqtt_host",
    help = "MQTT host to connect to (default: don't connect)",
    default = None,
)
parser.add_option(
    "", "--mqtt-port",
    dest = "mqtt_port",
    help = "MQTT port to connect to (default: 1883)",
    default = 1883,
)
parser.add_option(
    "", "--mqtt-topic",
    dest = "mqtt_topic",
    help = "MQTT topic (default: iot)",
    default = "iot",
)
parser.add_option(
    "", "--reloader",
    default = False,
    action = "store_true",
    dest = "reloader",
    help = "",
)
(options, args) = parser.parse_args()

class OptionException(Exception):
    pass

def load_module(code_path):
    try:
        try:
            code_dir = os.path.dirname(code_path)
            code_file = os.path.basename(code_path)

            fin = open(code_path, 'rb')

            return  imp.load_source(md5.new(code_path).hexdigest(), code_path, fin)
        finally:
            try: fin.close()
            except: pass
    except ImportError, x:
        traceback.print_exc(file = sys.stderr)
        raise
    except:
        traceback.print_exc(file = sys.stderr)
        raise

if __name__ == '__main__':
    try:
        if not args:
            raise   OptionException, "<module> required after arguments"
        
        SERVE_MODULE = args[0]
    except SystemExit:
        raise
    except OptionException, s:
        print >> sys.stderr, "%s: %s\n" % ( sys.argv[0], s, )
        parser.print_help(sys.stderr)
        sys.exit(1)
    except Exception, x:
        iotdb_log.log(exception = True)
        parser.print_help(sys.stderr)
        sys.exit(1)

    if options.pidfile:
        with open(options.pidfile, 'w') as fout:
            fout.write("%d\n" % os.getpid())

    if options.mqtt_host:
        import mosquitto


    def render_json(thing, d):
        bottle.response.content_type = MIME_JSON
        bottle.response.add_header("Access-Control-Allow-Origin", "*")
        bottle.response.add_header("Access-Control-Allow-Methods", "GET, PUT, POST")
        bottle.response.add_header("Access-Control-Allow-Headers", "Content-Type")
        return json.dumps(thing._serialize_out(d), sort_keys = True, indent = 5)

    def render(thing, d):
        return render_json(thing, d)

    def on_update(thing, url_path, old_stated, new_stated):
        if old_stated == new_stated:
            return

        iotdb_log.log("on_update", name=thing.name, url_path=url_path, old_stated=old_stated, new_stated=new_stated)

        if not options.mqtt_host:
            return

        url_path = url_path.split("/")
        mqtt_topic = options.mqtt_topic.split("/")

        def diffd(od, nd, dpath):
            for key in set(od.keys() + nd.keys()):
                ovalue = od.get(key)
                nvalue = nd.get(key)
                ## iotdb_log.log(ndpath=dpath + [ key ], ovalue=ovalue, nvalue=nvalue)
                if ovalue == nvalue:
                    continue

                ndpath = dpath + [ key ]
                if isinstance(ovalue, dict) and isinstance(nvalue, dict):
                    for r in diffd(ovalue, nvalue, ndpath):
                        yield r
                else:
                    iotdb_log.log("change", dpath=ndpath, ovalue=ovalue, nvalue=nvalue)
                    yield ndpath, nvalue

        mqttc = None
        for ndpath, nvalue in diffd(old_stated, new_stated, []):
            path = mqtt_topic + url_path + ndpath
            path = filter(None, path)

            topic = "/".join(path)
            message = json.dumps(nvalue)

            if not mqttc:
                mqttc = mosquitto.Mosquitto()
                mqttc.connect(options.mqtt_host, int(options.mqtt_port), 60)

            mqttc.publish(topic, message, 1)
            iotdb_log.log("MQTT.publish", 
                topic=topic, 
                msg=message, 
                mqtt_host=options.mqtt_host, 
                mqtt_port=options.mqtt_port,
            )

    serve_module = load_module("%s.py" % SERVE_MODULE)
    serve_class = getattr(serve_module, "Thing")
    serve_object = serve_class(name=SERVE_MODULE, on_update=on_update, render=render)

    if options.bonjour:
        bottle.run(
            serve_object.application(), 
            server=thing.BonjourServer(SERVE_MODULE), 
            reloader=options.reloader,
        )
    elif options.flup:
        bottle.run(
            serve_object.application(), 
            server='flup',
            port=int(options.port),
            host=options.host,
            reloader=False,
        )
    elif options.port:
        bottle.run(
            serve_object.application(), 
            server=thing.PortServer(SERVE_MODULE, port=int(options.port), host=options.host), 
            port=int(options.port),
            host=options.host,
            reloader=options.reloader,
        )
    else:
        bottle.run(
            serve_object.application(), 
            server=thing.PortServer(SERVE_MODULE, port=int(serve_object.port), host=options.host), 
            port=int(serve_object.port),
            host=options.host,
            reloader=options.reloader,
        )
