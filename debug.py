import sys
import traceback
from IPython import embed as shell
from IPython.core import ultratb
# ultratrace = ultratb.FormattedTB(mode='Plain',color_scheme='Linux',
# call_pdb=0)
ultratrace = ultratb.VerboseTB()
# sys.excepthook = ultratrace
from IPython.core.debugger import Tracer

debug = Tracer('Linux')


def trace():
    ultratrace(sys.exc_info())


def trace_all():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    # print "The exc_type, exc_value, exc_traceback is been printed"
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    traceback.print_exception(exc_type, exc_value)

# def trace_formatted() :
#    exc_type , exc_value, exc_traceback = sys.exc_info()
#    #print repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
#
#    traceback.print_exception(exc_type, exc_value )
