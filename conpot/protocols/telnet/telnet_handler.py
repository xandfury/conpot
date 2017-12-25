# To run a green server, import gevent and the green version of telnetsrv.
import gevent, gevent.queue, gevent.server
import socket
from telnetsrv.telnetsrvlib import TelnetHandlerBase, command
import logging as logger
import sys
import time

from lxml import etree
import conpot.core as conpot_core

# Supress errors when the client disconnects
import gevent.hub
gevent.hub.Hub.NOT_ERROR=(Exception,)

logger.getLogger('').setLevel(logger.DEBUG)

class ConnectionCount(object):
    '''A simple server class that just keeps track of a connection count.'''
    def __init__(self):
        # Var to track the total connections.
        self.connection_count = 0

        # Dictionary to track individual connections.
        self.user_connect = {}

    def new_connection(self, username):
        '''Register a new connection by username, return the count of connections.'''
        self.connection_count += 1
        try:
            self.user_connect[username] += 1
        except:
            self.user_connect[username] = 1
        return self.connection_count, self.user_connect[username]


class TelnetHandler(TelnetHandlerBase):
    '''A telnet server handler using Gevent'''
    # Create the instance of the server within the class for easy use
    myserver = ConnectionCount()
    TELNET_BANNER = ''
    template_directory = ''

    def __init__(self, request, client_address, server=None):
        # Create a green queue for input handling
        self.cookedq = gevent.queue.Queue()
        self.client_address = client_address

        # Whether we need the user to enter user/pass
        self.authNeedUser = True
        self.authNeedPass = True
        self.username = None
        self.password = None
        # self.TELNET_BANNER = TELNET_BANNER
        self.timeout = 5
        # Call the base class init method
        TelnetHandlerBase.__init__(self, request, client_address, server)

    def setup(self):
        '''Called after instantiation'''
        TelnetHandlerBase.setup(self)
        # Spawn a greenlet to handle socket input
        # Note that inputcooker exits on EOF
        self.greenlet_ic = gevent.spawn(self.inputcooker)
        # Sleep for 0.5 second to allow options negotiation
        gevent.sleep(0.5)

    def handle(self):
        '''The actual service to which the user has connected.'''
        # This should overwrite TelnetHandlerBase.handler() because
        # we might want to write a more customized handler in future
        # This is nothing to do with the actual SocketStream handler.
        # It is just how we want to process/handle the commands entered
        # by the telnet user.
        if self.TELNET_BANNER:
            self.writeline(self.TELNET_BANNER)
        # authentication_ok() is a boolean in TelnetHandlerBase
        # on whether auth is success or failure
        if not TelnetHandlerBase.authentication_ok(self):
            return
        # start to init the socket
        self.session_start()
        while self.RUNSHELL:
            raw_input = self.readline(prompt=self.PROMPT).strip()
            self.input = self.input_reader(self, raw_input)
            self.raw_input = self.input.raw
            if self.input.cmd:
                cmd = self.input.cmd.upper()
                params = self.input.params
                if self.COMMANDS.has_key(cmd):
                    try:
                        self.COMMANDS[cmd](params)
                    except:
                        log.exception('Error calling %s.' % cmd)
                        (t, p, tb) = sys.exc_info()
                        if TelnetHandlerBase.handleException(t, p, tb):
                            break
                else:
                    self.writeerror("Unknown command '%s'" % cmd)
        logger.debug("Exiting handler")

    def finish(self):
        '''End this session'''
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            logger.info('Terminating client session from %s' %(self.client_address,))
            # Ensure the greenlet is dead
            self.greenlet_ic.kill()
        except Exception as e:
            logger.exception("{}: {}".format(type(e).__name__, e))

    def log(self):
        globalcount, usercount = TelnetHandler.myserver.new_connection( self.username )
        self.writeline('Incorrect username/password. Please try again.')
        logger.info('Incoming telnet connection from %s' % (self.client_address,))
        logger.info('User %s with password %s has attempted to have log in %s time(s). Total telnet login attempts #%d' % (self.username, self.password, usercount, globalcount))

    def authCallback(self, username, password):
        '''Called to validate the username/password.'''
        # TODO: Increase fuctionality in future releases
        self.username = username
        self.password = password
        self.log()
        # Terminate the connection for now
        self.finish()

    # -- Green input handling functions --
    # -- from https://github.com/ianepperson/telnetsrvlib/blob/fac52a4a333c2d373d53d295a76a0bbd71e5d682/telnetsrv/green.py --
    def getc(self, block=True):
        '''Return one character from the input queue'''
        try:
            return self.cookedq.get(block)
        except gevent.queue.Empty:
            return ''

    def inputcooker_socket_ready(self):
        '''Indicate that the socket is ready to be read'''
        return gevent.select.select([self.sock.fileno()], [], [], 0) != ([], [], [])

    def inputcooker_store_queue(self, char):
        '''Put the cooked data in the input queue (no locking needed)'''
        if type(char) in [type(()), type([]), type("")]:
            for v in char:
                self.cookedq.put(v)
        else:
            self.cookedq.put(char)


class SubTelnetHandler(TelnetHandler):
    '''Class is used to create customized dialog flows/commands
    for the telnet defined server'''
    # This class is like a Processor class that defines
    # all the commands that would be present in the conpot's
    # telnet server.

    # Method invoked after authentication is successful
    def session_start(self):
        '''Called after the user successfully logs in.'''
        pass

    def cmdHELP(self, params):
        '''The help command'''
        pass

    def cmdHISTORY(self, params):
        '''The history command'''
        pass

    def cmdEXIT(self, params):
        """
        Exit the command shell
        """
        self.RUNSHELL = False

    def session_end(self):
        '''Called after the user successfully logs in.'''
        pass

    def writeerror(self, text):
        '''Called to write any error information (like a mistyped command).
        Add a splash of color using ANSI to render the error text in red.
        see http://en.wikipedia.org/wiki/ANSI_escape_code'''
        TelnetServer.writeerror(self, "\x1b[91m%s\x1b[0m" % text )

    # @classmethod
    # def streamserver_handle(self, sock, address):
    #     '''Translate this class for use in a StreamServer'''
    #     sock.settimeout(self.timeout)
    #     session = conpot_core.get_session('telnet', address[0], address[1])

    #     logger.info(
    #         'New Telnet connection from %s:%s. (%s)',
    #         address[0], address[1], self.session.id)
    #     self.session.add_event({'type': 'NEW_CONNECTION'})
    #     self.start_time = time.time()

    #     super().streamserver_handle(sock, address)

    #     logger.info('Telnet client terminated connection.'
    #                 ' (%s)', self.session.id)
    #     self.session.add_event({'type': 'CONNECTION_TERMINATED'})
