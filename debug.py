import logging
import ipdb
import sys, traceback 
from traceback import format_exception

from IPython.core import ultratb
ultratrace = ultratb.FormattedTB(mode='Plain',color_scheme='Linux', call_pdb=0)

from ipdb import set_trace as debug

def trace():
    tyep, value, traceback = sys.exc_info()
    ultratrace(tyep,value,traceback)
    logging.error(format_exception(tyep,value,traceback))
