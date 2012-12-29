#!/usr/bin/env python
import sys
sys.path.append('.')
import unittest
from options import configure
import tornado.testing

TEST_MODULES = [
    #'test_asynccouch',
    'test_couchadapter',
]


def all():
    try:
        return unittest.defaultTestLoader.loadTestsFromNames(TEST_MODULES)
    except AttributeError, e:
        if "'module' object has no attribute 'test_" in str(e):
            # most likely because of an import error
            for m in TEST_MODULES:
                __import__(m, globals(), locals())
        raise

if __name__ == '__main__':
    configure()
    tornado.testing.main()
