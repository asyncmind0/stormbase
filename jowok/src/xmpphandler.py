import sys,os
import logging
import getpass
from sleekxmpp.xmlstream import ElementBase

import sleekxmpp

loggerhandler = None

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input

class Config(ElementBase):
    """
    In order to make loading and manipulating an XML config
    file easier, we will create a custom stanza object for
    our config XML file contents. See the documentation
    on stanza objects for more information on how to create
    and use stanza objects and stanza plugins.

    We will reuse the IQ roster query stanza to store roster
    information since it already exists.

    Example config XML:
      <config xmlns="sleekxmpp:config">
        <jid>component.localhost</jid>
        <secret>ssshh</secret>
        <server>localhost</server>
        <port>8888</port>

        <query xmlns="jabber:iq:roster">
          <item jid="user@example.com" subscription="both" />
        </query>
      </config>
    """

    name = "config"
    namespace = "sleekxmpp:config"
    interfaces = set(('jid', 'secret', 'server', 'port'))
    sub_interfaces = interfaces

class JowokBot(sleekxmpp.ClientXMPP):

    """
    A simple SleekXMPP bot that will echo messages it
    receives, along with a short thank you message.
    """

    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can intialize
        # our roster.
        self.add_event_handler("session_start", self.start)

        # The message event is triggered whenever a message
        # stanza is received. Be aware that that includes
        # MUC messages and error messages.
        self.add_event_handler("message", self.message)
        #ptypes = ['available', 'away', 'dnd', 'xa', 'chat',
        #          'unavailable', 'subscribe', 'subscribed',
        #          'unsubscribe', 'unsubscribed']

        #for ptype in ptypes:
        #    handler = lambda p: logging.info(p)
        #    self.add_event_handler('presence_%s' % ptype, handler)
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0060') # PubSub
        self.register_plugin('xep_0199') # XMPP Ping
        # If you are working with an OpenFire server, you may need
        # to adjust the SSL version used:
        # self.ssl_version = ssl.PROTOCOL_SSLv3

        # If you want to verify the SSL certificates offered by a server:
        # self.ca_certs = "path/to/ca/cert"

    def presence(self, event):
        print event

    def start(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an intial
        presence stanza.

        Arguments:
            event -- An empty dictionary. The session_start
                     event does not provide any additional
                     data.
        """
        self.get_roster()
        self.send_presence()

    def message(self, msg):
        """
        Process incoming message stanzas. Be aware that this also
        includes MUC messages and error messages. It is usually
        a good idea to check the messages's type before processing
        or sending replies.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        if msg['type'] in ('chat', 'normal'):
            msg.reply("Thanks for sending\n%(body)s" % msg).send()

class XmppHandler(logging.Handler):
    def __init__(self, xmppclient, recepients, level=logging.NOTSET):
        super(XmppHandler,self).__init__(level)
        self.recepients=recepients
        self.xmppclient = xmppclient

    def emit(self, record):
        message = record.getMessage()
        for recepient in self.recepients:
            self.xmppclient.send_message(mto=recepient,
                    mbody=message, mtype='chat')


