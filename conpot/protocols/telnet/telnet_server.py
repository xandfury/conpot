#!/usr/bin/python
# Telnet handler concrete class using green threads
# Method to start the server
# Method to stop the server
# Method to handle the connections
# __init__()

import logging
import os

logger = logging.getLogger(__name__)

from telnet_handler import SubTelnetHandler

class TelnetServer(object):
    def __init__(self, template, template_directory, args):
        self.template = template
        self.template_directory = template_directory
        # Locate the template
        self.template = (self.template, os.path.join(self.template_directory, 'telnet'))
        # Retrieve banner from template
        self._get_template(template)
        self.server_port = None
        # Create the instance of the server within the class for easy use
        self.Handler = SubTelnetHandler
        self.server_stopped = False
        self.telnet_server = None

    def _get_template(self, template):
        dom = etree.parse(template)
        try:
            self.Handler.TELNET_BANNER = dom.xpath('//telnet/device_info/banner/text()')[0].lower()
        except ValueError:
            logger.error('Conpot telnet initialization failed due to incorrect'
                         ' settings. Check the telnet template file')
            sys.exit(3)


    def start(self, host, port):
        connection = (host, port)
        self.telnet_server = gevent.server.StreamServer(connection, self.Handler)
        logger.info('Telnet server started on: %s', connection)
        while not self.server_stopped:
            self.telnet_server.serve_forever()

    def stop(self):
        logger.debug('Stopping Telnet server')
        # self.finish()
        self.server_stopped = True
        self.telnet_server.stop()


# if __name__ == '__main__':
    # Parse the input arguments
    # Normally, these would be down in "if __name__ == '__main__'", but we need to know green-vs-threaded for the base class and other imports
    # parser = argparse.ArgumentParser( description='Run a telnet server.')
    # parser.add_argument( 'port', metavar="PORT", type=int, help="The port on which to listen on." )
    # parser.add_argument( '-g', '--green', action='store_const', const=True, default=False, help="Run with cooperative multitasking using Gevent library.")
    # console_args = parser.parse_args()

    # TELNET_PORT_BINDING = console_args.port


    # TELNET_IP_BINDING = '' #all
    # # The SocketServer needs *all IPs* to be 0.0.0.0
    # if not TELNET_IP_BINDING:
    #     TELNET_IP_BINDING = '0.0.0.0'
