#
#   thing.py
#
#   David Janes
#   IOTDB
#   2013-12-09
#
#   Base class for implementing things
#

import sys
import json
import select
import sys
import os
import pprint
import re

import bottle

import iotdb_log

MIME_JSON = "application/json"
## MIME_JSON = "text/plain"

def served(name, d=None, update=False):
    served_root = os.path.join(os.environ["HOME"], ".iot-served")
    served_path = os.path.join(served_root, name)

    if not os.path.isdir(served_root):
        os.makedirs(served_root)

    if d == None:
        if os.path.exists(served_path):
            with open(served_path, "r") as fin:
                return json.load(fin)
    else:
        if update and os.path.exists(served_path):
            od = {}
            with open(served_path, "r") as fin:
                od = json.load(fin)

            od.update(d)
            d = od

        with open(served_path, "w") as fout:
            json.dump(d, fout, sort_keys = True, indent = 2)
            ## print >> fout, json.dumps(d, sort_keys = True, indent = 2)

class PortServer(bottle.ServerAdapter):
    def __init__(self, name, save=True, **ad):
        bottle.ServerAdapter.__init__(self, **ad)

        self.name = name
        self.save = save

    def run(self, handler): # pragma: no cover
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler

        srv = make_server(self.host, self.port, handler, **self.options)
        iotdb_log.log("PortServer: ACTUALLY listening", on = "http://%s:%s/" % ( self.host, self.port, ))

        if self.save:
            served(self.name, { "url" : "http://%s:%s/" % ( self.host, self.port, ), })

        srv.serve_forever()

class BonjourServer(bottle.ServerAdapter):
    def __init__(self, name, regtype="_json._tcp.", save=True):
        bottle.ServerAdapter.__init__(self)

        self.name = name
        self.regtype = regtype
        self.save = save

    def run(self, handler): # pragma: no cover
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler

        srv = make_server("0.0.0.0", 0, handler, **self.options)
        port = srv.socket.getsockname()[1]
        iotdb_log.log("BonjourServer: ACTUALLY listening", on = "http://0.0.0.0:%s/" % ( port, ))

        if self.save:
            served(self.name, { "url" : "http://0.0.0.0:%s/" % ( port, ), })

        self.register_bonjour(
            port=port,
            name=self.name,
            regtype=self.regtype,
        )

        srv.serve_forever()

    def on_service_register(self, sdRef, flags, errorCode, name, regtype, domain):
        import pybonjour
        if errorCode == pybonjour.kDNSServiceErr_NoError:
            bonjour="%s.%s%s" % ( name, regtype, domain, )
            iotdb_log.log("BonjourServer: registered service", 
                name=name, 
                regtype=regtype,
                domain=domain,
                bonjour=bonjour,
            )
            if self.save:
                served(self.name, { "bonjour":bonjour }, update=True)

    def register_bonjour(self, port, name, regtype):
        import pybonjour
        sdRef = pybonjour.DNSServiceRegister(
            name=name,
            regtype=regtype,
            port=port,
            callBack=self.on_service_register,
        )

        try:
            try:
                while True:
                    ready = select.select([sdRef], [], [])
                    if sdRef in ready[0]:
                        pybonjour.DNSServiceProcessResult(sdRef)
                        break
            except KeyboardInterrupt:
                pass
        finally:
            pass ## sdRef.close()

def validate_ranged(new_value, old_value, min, max):
    if new_value < min:
        return min
    elif new_value > max:
        return max
    else:
        return new_value

def validate_rgb(new_value, old_value):
    new_value = new_value.upper()
    if re.match("^#[0-9A-F]{6}$", new_value):
        return new_value
    else:
        return old_value

class Thing(object):
    """You must define self.stated in a subclass"""

    name = "unknown"
    port = 9100
    stated = {}
    validated = {}

    def __init__(self, name=None, on_update=None, render=None):
        self.stated = dict(self.stated)
        self.on_update = on_update
        self.render = render or self.render_json

        if name:
            self.name = name

    def render_json(self, thing, d):
        bottle.response.content_type = MIME_JSON
        return json.dumps(thing._serialize_out(d), sort_keys = True, indent = 2)

    def validate(self):
        pass

    def _serialize_out(self, o):
        if isinstance(o, dict):
            no = {}
            for key, value in o.iteritems():
                no[key] = self._serialize_out(value)

            return no
        elif isinstance(o, list):
            nos = []
            for value in o.iteritems():
                nos.append(self._serialize_out(no))

            return nos
        elif isinstance(o, Thing):
            return self._serialize_out(o.stated)
        else:
            return o

    def _subthing(self, path):
        if isinstance(path, basestring):
            path = filter(None, path.split("/"))

        thing = self

        for part in path:
            ## iotdb_log.log(stated = thing.stated, part=part)
            thing = thing.stated.get(part)
            if not thing:
                return None
            elif isinstance(thing, dict):
                t = Thing()
                t.stated = thing
                thing = t
            elif isinstance(thing, Thing):
                pass
            else:
                return None

        return thing

    def _update(self, updated, stated = None):
        if stated == None:
            stated = self.stated

        for key, new_value in updated.iteritems():
            if isinstance(new_value, list):
                iotdb_log.log("cannot deal with a 'list' value -- ignoring", key=key, value=new_value)
                continue
            elif isinstance(new_value, dict):
                subthing = stated.get(key)
                if isinstance(subthing, dict):
                    for subkey, sub_old_value in subthing.iteritems():
                        sub_new_value = new_value.get(subkey)
                        if sub_new_value == None:
                            continue
                        
                        if isinstance(sub_old_value, Thing):
                            sub_old_value._update(sub_new_value)
                        else:
                            iotdb_log.log("don't know what to do here yet", subkey=subkey, sub_new_value=sub_new_value, sub_old_value=sub_old_value) ;
                        ## self._update(updated, subvalue)
                elif isinstance(subthing, Thing):
                    subthing._update(new_value)
                else:
                    iotdb_log.log("nested state was not a Thing -- ignoring", key=key, value=new_value, subthing=subthing)
                    continue
            elif new_value == None:
                iotdb_log.log("cannot deal with None -- ignoring", key=key, value=new_value)
                continue
            else:
                old_value = stated.get(key)
                if old_value == None:
                    iotdb_log.log("key not found -- ignoring", key=key, value=new_value, stated=stated)
                    continue

                try:
                    new_value = old_value.__class__(new_value)
                    assert(new_value.__class__ == old_value.__class__)
                except:
                    iotdb_log.log("new_value could not be coerced to type of old_value",
                        exception = True, old_value = old_value, new_value = new_value)
                    continue

                validatet = self.validated.get(key)
                if validatet:
                    validate_f = validatet[0]
                    validate_args = validatet[1:]

                    new_value = validate_f(new_value, old_value, *validate_args)

                if new_value == old_value:
                    continue

                stated[key] = new_value

        self.validate();

    def application(self):
        app = bottle.Bottle()

        @app.route('/<path:path>', method=['OPTIONS'])
        def options(path = ""):
            bottle.response.content_type = MIME_JSON
            bottle.response.add_header("Access-Control-Allow-Origin", "*")
            bottle.response.add_header("Access-Control-Allow-Methods", "GET, PUT, POST")
            bottle.response.add_header("Access-Control-Allow-Headers", "Content-Type")
            return json.dumps({})

        @app.get('/')
        @app.get('/<path:path>')
        def get(path = ""):
            jsond = {}
            match = re.match("^(.*)/([^=]+)=(.*)", path)
            if match:
                path = match.group(1)

                key = match.group(2)
                value = match.group(3)
                if value == "true": value = True
                elif value == "false": value = False

                jsond = {
                    key : value,
                }
            
            subthing = self._subthing(path)
            if not subthing:
                bottle.response.content_type = "text/plain"
                return "Not found\n"

            if jsond:
                if self.on_update:
                    old_stated = self._serialize_out(subthing.stated)

                subthing._update(jsond)

                if self.on_update:
                    new_stated = self._serialize_out(subthing.stated)
                    self.on_update(self, path, old_stated, new_stated)

            return self.render(self, subthing.stated)

        @app.put('/')
        @app.put('/<path:path>')
        @app.post('/')
        @app.post('/<path:path>')
        def put(path  = ""):
            subthing = self._subthing(path)
            if not subthing:
                bottle.response.content_type = "text/plain"
                return "Not found\n"

            if not bottle.request.json:
                iotdb_log.log("soft error - no JSON request")
            else:
                if self.on_update:
                    old_stated = self._serialize_out(subthing.stated)

                subthing._update(bottle.request.json)

                if 0: iotdb_log.log(name=self.name, 
                    new_stated=self._serialize_out(subthing.stated), 
                    request=bottle.request.json,
                )

                if self.on_update:
                    new_stated = self._serialize_out(subthing.stated)
                    self.on_update(self, path, old_stated, new_stated)

            return self.render(self, subthing.stated)

        ## end of 'application'
        return app
