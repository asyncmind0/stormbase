#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zmq
from zmq.eventloop import ioloop, zmqstream
import tornado
import tornado.web
import tornado.httpserver
import pickle
import time
import os
from xmpphandler import XmppHandler, JowokBot
from optparse import OptionParser
import logging

loggerhandler = None
ioloop.install()

def parse_options():
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    # Component name and secret options.
    optp.add_option("-c", "--config", help="path to config file",
                    dest="config", default="conf/jabber.xml")
    optp.add_option("-t", "--target", help="target jid to send log envents",
                    dest="targetjids", default=None)
    optp.add_option("-u", "--urls", help="urls to listen on for messages",
                    dest="listenurls", default=None)

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config.read('conf/jowok.cfg')
    #import ipdb; ipdb.set_trace()


    if opts.jid is None:
        opts.jid = config.get('jabber','jid')
    if opts.password is None:
        opts.password = config.get('jabber','secret')
    if opts.targetjids is None:
        opts.targetjids = config.get('jabber','recepients')
    if opts.listenurls is None:
        opts.listenurls = config.get('mq','urls')

    return opts

def main():
    opts = parse_options()
    xmpp = JowokBot(opts.jid, opts.password)
    if xmpp.connect():
        xmpp.process(threaded=True)
    else:
        logging.debug("Unable to connect.")
        exit()

    while not xmpp.sessionstarted:
        time.sleep(2)

    addrs = [ chunk.strip() for chunk in opts.listenurls.split(',') ]
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, "")
    for addr in addrs:
        logging.debug("Connecting to: %s"% addr)
        socket.connect(addr)

    def on_recv(msgs):
        #msg = socket.recv_pyobj()
        for msg in msgs:
            msgl = pickle.loads(msg.bytes)
            message =  "%s: %s" % (msgl[1], msgl[0])
            global loggerhandler
            if loggerhandler:
                loggerhandler.write_message(message)

    tloop = tornado.ioloop.IOLoop.instance()
    recepients = [ chunk.strip() for chunk in opts.targetjids.split(',') ]
    logging.getLogger().addHandler(XmppHandler(xmpp,recepients))

    stream = zmqstream.ZMQStream(socket, tloop)
    stream.on_recv(on_recv, copy=False)

    from tornado.websocket import WebSocketHandler


    class TestHandler(tornado.web.RequestHandler):
        def get(self):
            self.render('logger.html')

    class CometHandler(WebSocketHandler):
        def open(self):
            global loggerhandler
            loggerhandler = self
            logging.debug( "Websocket opened")

        def on_message(self, message):
            logging.debug( 'got message %s' % message)
            self.write_message("You said: %s" % message)

        def on_close(self):
            logging.debug( "Websocket closed")

    application = tornado.web.Application(
            [
                (r"/", TestHandler),
                (r"/comet", CometHandler),
                ],
            template_path=os.path.join(os.path.dirname(__file__), "../templates"),
            gzip=True,
            debug=True
            )
    
    http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
    http_server.listen(8888)
    tloop.start()


    logging.debug( 'exiting')
    xmpp.disconnect(wait=True)


if __name__ == '__main__':
    main()
