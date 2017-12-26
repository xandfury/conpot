# To run a green server, import gevent and the green version of telnetsrv.
import gevent, gevent.queue, gevent.server
import socket
# from telnetsrv.telnetsrvlib import TelnetHandlerBase, command
from telnetsrv.green import TelnetHandler as TelnetHandlerBase, command
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
    timeout = 5
    def __init__(self, request, client_address, server=None):
        # Create a green queue for input handling
        self.client_address = client_address

        # Whether we need the user to enter user/pass
        self.authNeedUser = True
        self.authNeedPass = True
        self.username = None
        self.password = None

        # Call the base class init method
        TelnetHandlerBase.__init__(self, request, client_address, server)

    def handle(self):
        '''The actual service to which the user has connected.'''
        # This has nothing to do with the actual SocketStream handler.
        # It is just how we want to process/handle the commands entered
        # by the client.
        if self.TELNET_BANNER:
            self.writeline(self.TELNET_BANNER)
        # authentication_ok() is a boolean in TelnetHandlerBase
        # on whether auth is success or failure
        if not TelnetHandlerBase.authentication_ok(self):
            return
        # start the session
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
        # Terminates the session as the client/server disconnects
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            logger.info('Terminating client session from %s' %(self.client_address,))
            # Ensure the greenlet is dead
            self.greenlet_ic.kill()
        except socket.error as e:
            import errno
            if e.errno == errno.EINVAL:
                pass
            self.sock.close()
            self.session_end()
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

    @classmethod
    def streamserver_handle(cls, sock, address):
        '''Translate this class for use in a StreamServer'''
        sock.settimeout(cls.timeout)
        session = conpot_core.get_session('telnet', address[0], address[1])

        cls.start_time = time.time()
        logger.info('New Telnet connection from {0}:{1}. ({2})'.format(address[0], address[1], session.id))
        session.add_event({'type': 'NEW_CONNECTION'})

        request = cls.false_request()
        request._sock = sock
        server = None
        logger.debug("Accepted connection, starting telnet session.")
        try:
            cls(request, address, server)
        except socket.timeout:
            session.add_event({'type': 'CONNECTION_LOST'})
            logger.debug('Socket timeout, remote: {0}. ({1})'.format(address[0], session.id))
        except socket.error:
            session.add_event({'type': 'CONNECTION_LOST'})
            logger.debug('Connection reset by peer, remote: {0}. ({1})'.format(address[0], session.id))
        except Exception as e:
            logger.info('Exception caught {0}, remote: {1}. ({2})'.format(e, address[0], session.id))



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
