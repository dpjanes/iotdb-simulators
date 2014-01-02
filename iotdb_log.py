#
#   iotdb_log.py
#
#   David Janes
#   IOTDB
#   2013-10-15
#
#   Logging stuff
#
#   All the email stuff needs to be moved out
#

import sys
import pprint
import os
import json
import traceback
import time
import datetime
import inspect
import cStringIO as StringIO

def log(_message = "", **ad):
    __Log(_message, _trace_adjust = 1, **ad)

def _send_email(title, _message = ""):
    from django.core.mail import send_mail
    send_mail(
        subject='IOTDB: %s' % title, 
        message=_message,
        from_email='admin@iotdb.org',
        recipient_list=['iotdb@davidjanes.com'], 
        fail_silently=True
    )

def database_incident(_message, **ad):
    __Log(_message, _trace_adjust = 1, **ad)
    
def signin(username, status, **ad):
    """Call me when there's a signin"""
    __Log("user signin", username = username, _trace_adjust = 1, **ad)

    _send_email("user signin: %s (%s)" % ( username, status, ))

def signup(email, status, **ad):
    """Call me when there's a signup"""
    __Log("user signup", email = email, _trace_adjust = 1, **ad)

    _send_email("user signup: %s (%s)" % ( email, status, ))

#
#   This is the log function from pybm. 
#   More work should be done to make this pyton
#   logging compatible
#
def __Log(
    _message="", 
    _exception=False, 
    _logfile=None, 
    _logdir=None, 
    _severity="info", 
    _verbose=None, 
    _trace_adjust=0, 
    **args
):
	""" Log a message: _logdir and severity are synonyms, recomended severities are:
	    debug, info, warning, error, critical
	"""
	if _verbose and not __Log.verbose:
		return

	result = ""

	try:
		cout = StringIO.StringIO()
		print >> cout, "[log_entry]"
		if _logdir and os.path.exists( _logdir ):
			print >> cout, "[severity]", _severity
		else:
			print >> cout, "[severity]", _logdir or _severity
		print >> cout, "[date]", datetime.datetime.now().isoformat()[:19];
		try:
			caller = inspect.stack()[1 + _trace_adjust]

			print >> cout, "%s (%s:%d)" % ( caller[3], caller[1], caller[2], )
		except KeyboardInterrupt:
			raise
		except IndexError:
			pass
		except:
			print >> cout, "(exception gettings stack)"
			traceback.print_exc()

		if _message:
			print >> cout, "  message: %s" % ( _message, )

		items = args.items()
		items.sort()

		if _exception:
			exc_type, exc_value, exc_traceback = sys.exc_info()
			items.append(("traceback-type", exc_type))
			items.append(("traceback-value", exc_value))
			if not args.get("no_stack"):
				items.append(("traceback-stack", traceback.extract_tb(exc_traceback)))

		if args.get("stack_trace"):
			stack = inspect.stack()
			for frame in stack:
				print >> cout, "  %s (%s:%d)" % ( frame[3],  frame[1], frame[2], )

		for key, value in items:
			try:
				if isinstance(value, ( dict, list, )) or type(value) in [ types.GeneratorType, types.XRangeType, ]:
					print >> cout, "  %s:" % ( key, )
					try:
						for line in pprint.pformat(value).split("\n"):
							print >> cout, "   ", line
					except KeyboardInterrupt:
						raise
					except:
						print >> cout, "  [UN-PPRINT-ABLE DATA]"
				elif isinstance(value, sets.Set):
					print >> cout, "  %s: (set):" % ( key, )
					try:
						for line in value:
							if type(line) == types.UnicodeType:
								print >> cout, ".  %s" % ( line.encode('latin-1', 'replace') )
							else:
								print >> cout, ".  %s" % ( line, )
					except KeyboardInterrupt:
						raise
					except Error, x:
						print >> cout, "  [UN-PPRINT-ABLE DATA]", x
				elif type(value) in types.StringTypes and value.find("\n") > -1:
					print >> cout, "  %s: ---" % ( key, )
					for line in value.split("\n"):
						if type(line) == types.UnicodeType:
							print >> cout, ".  %s" % ( line.encode('latin-1', 'replace') )
						else:
							print >> cout, ".  %s" % ( line )
					print >> cout, "  -------"
				elif type(value) == types.UnicodeType:
					print >> cout, "  %s: %s" % ( key, value.encode('latin-1', 'replace') )
				else:
					print >> cout, "  %s: %s" % ( key, value )
			except:
				print >> cout, "  %s: [bad unicode data]"

		print >> cout, "[end_log_entry]"

		result = cout.getvalue()

		if _logfile or _logdir:
			if _logdir:
				# an absolute path for '_logdir' will override the standard ~/logs
				_logfile = _logfile or os.getenv("BM_CRITICAL_LOG", None)
				if not _logfile:
					tt = time.localtime()
					_logfile = os.path.join(
						os.environ["HOME"],
						"logs",
						_logdir,
						"%04d%02d%02d.log" % ( tt[0], tt[1], tt[2] ),
					)

			try: os.makedirs(os.path.dirname(_logfile))
			except: pass

			try:
				lout = open(_logfile, "a")
				lout.write(result)
				sys.stderr.write(result)
			except KeyboardInterrupt:
				raise
			except:
				pass
		else:
			sys.stderr.write(result)

			if sys.stderr.isatty():
				sys.stderr.write("\n")

		sys.stderr.flush()

	finally:
		try: cout.close()
		except: pass

		if _logfile:
			try: lout.close()
			except: pass

	return	result

__Log.verbose = False

__Log.SEVERITY_DEBUG = "debug"
__Log.SEVERITY_INFO = "info"
__Log.SEVERITY_WARNING = "warning"
__Log.SEVERITY_ERROR = "error"
__Log.SEVERITY_CRITICAL = "critical"

log("hi there")
