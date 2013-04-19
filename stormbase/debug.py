import sys
import traceback
from IPython import embed as shell
from IPython.core import ultratb
# ultratrace = ultratb.FormattedTB(mode='Plain',color_scheme='Linux',
# call_pdb=0)
ultratrace = ultratb.VerboseTB()
# sys.excepthook = ultratrace
from IPython.core.debugger import Tracer

#import pudb
#debug = pudb.set_trace
debug = Tracer('Linux')


def trace():
    ultratrace(sys.exc_info())


def trace_all():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    # print "The exc_type, exc_value, exc_traceback is been printed"
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    traceback.print_exception(exc_type, exc_value)


# code snippet, to be included in 'sitecustomize.py'
def info(type, value, tb):
    if hasattr(sys, 'ps1') or not sys.stderr.isatty():
        # we are in interactive mode or we don't have a
        # tty-like
        # device, so we call the default hook
        sys.__excepthook__(type, value, tb)
    else:
        # we are NOT in interactive mode, print the
        # exception...
        traceback.print_exception(type, value, tb)
        print
        # ...then start the debugger in
        # post-mortem mode.
        debug()


def set_except_hook():
    sys.excepthook = info
# def trace_formatted() :
#    exc_type , exc_value, exc_traceback = sys.exc_info()
#    #print repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
#
#    traceback.print_exception(exc_type, exc_value )
