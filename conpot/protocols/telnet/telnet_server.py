import logging

# For debugging
logging.basicConfig()

import os
from lxml import etree
from gevent.server import StreamServer

logger = logging.getLogger(__name__)

from telnet_handler import SubTelnetHandler

class TelnetServer(object):
    def __init__(self, template, template_directory, args):
        self.template = template
        self.template_directory = template_directory

        # for debugging. Delete this after done debug
        self.template = (self.template_directory + self.template)

        self.Handler = SubTelnetHandler
        # Retrieve banner from template
        # TODO: change to get template data
        self.Handler.TELNET_BANNER = self._get_banner(self.template)

        self.telnet_server = None

    def _get_banner(self, template):
        dom = etree.parse(template)
        try:
            TELNET_BANNER = dom.xpath('//telnet/device_info/banner/text()')[0].lower()
        except ValueError:
            logger.error('Conpot telnet initialization failed due to incorrect'
                         ' settings. Check the telnet template file')
            sys.exit(3)
        return TELNET_BANNER


    def start(self, host, port):
        connection = (host, port)
        # TODO: write a custom handler
        self.telnet_server = StreamServer(connection, self.Handler.streamserver_handle)
        # self.telnet_server = StreamServer(connection, self.handler)
        logger.info('Telnet server started on: %s', connection)
        self.telnet_server.serve_forever()

    def stop(self):
        logger.debug('Stopping Telnet server')
        self.telnet_server.stop()


# ---- For debugging ----
if __name__ == '__main__':
    protocol_name = 'telnet'
    root_template_directory = '/usr/local/lib/python2.7/dist-packages/Conpot-0.5.1-py2.7.egg/conpot/templates/default/'
    template_base = os.path.join(root_template_directory, protocol_name)
    template_base = template_base + '/'
    telnet = TelnetServer('telnet.xml', template_base, None)
    try:
        telnet.start('0.0.0.0', 9999)
    except KeyboardInterrupt:
        telnet.stop()
