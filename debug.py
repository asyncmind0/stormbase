import logging
import sys, traceback 
from traceback import format_exception

from IPython.core import ultratb, debugger
ultratrace = ultratb.FormattedTB(mode='Plain',color_scheme='Linux', call_pdb=0)

debug = debugger.Tracer()

def trace():
    tyep, value, traceback = sys.exc_info()
    ultratrace(tyep,value,traceback)
    logging.error(format_exception(tyep,value,traceback))
