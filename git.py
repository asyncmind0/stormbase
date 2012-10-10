#!/usr/bin/env python
import os
import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.options
from tornado.options import define, options

from tornado.ioloop import PeriodicCallback
from git import *

import logging


class CodeReloadOnCommit(PeriodicCallback):
    def __init__(self, ioloop, modules):
        self.modules = modules
        PeriodicCallback.__init__(self, self.reload_server, 5000, ioloop)
        self.repo = Repo("./")
        self.prev_head = self.repo.active_branch.commit
        logging.debug("Starting with commit " + str(self.prev_head)
                      + "\n" + self.prev_head.summary)

    def reload_server(self):
        head = self.repo.active_branch.commit
        if str(self.prev_head) != str(head):
            logging.debug("Reloading " + str(head) + "\n" + head.summary)
            self.prev_head = head
            for module in self.module:
                reload(module)
