#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function

import os
import sys

import time
import signal

import gevent
from gevent import monkey
# this needs to be AFTER python imports, but BEFORE package imports
monkey.patch_all()


from pyftpdlib.handlers import FTPHandler
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.servers import FTPServer


class cwd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


# Outside the class to be able to easily pickle it
def ftpd_block(address, authorizer, root_path):
    """
    runs and block until signal is caught
    :return:
    """
    FTPHandler.banner = 'conpot ftp server'
    try:
        with cwd(root_path):
            print("FTP Server is now providing {root_path} on {address[0]}:{address[1]} ...".format(**locals()))
            FTPHandler.authorizer = authorizer
            server = FTPServer(address, FTPHandler)
            # to test that exceptions raised log properly
            # raise StandardError("BAAAAAH")
            # we're in a green thread so no issue there... but it is more complicated between processes
            server.serve_forever()
    except OSError as ose:
        print(ose)
    except KeyboardInterrupt:
        print("FTP Server stopped by Keyboard Interrupt !")
    except SystemExit:
        print("FTP Server stopped by System Exit !")
    return 0


class FTPTestServer(object):
    def __init__(self, ip='0.0.0.0', port=2111, root_path=None):
        ip = ip or "127.0.0.1"
        self.address = (ip, port)
        self.root_path = root_path or os.getcwd()

        # TODO : add user authentication
        self.authorizer = DummyAuthorizer()
        self.authorizer.add_anonymous(self.root_path, perm="elradfmw")  # Ref : https://pythonhosted.org/pyftpdlib/api.html

        self.gth = None

    @property
    def ip(self):
        return self.address[0]

    @property
    def port(self):
        return self.address[1]

    def start(self):
        """
        start the server in a child process
        :return:
        """
        # making sure to kill everything before shutting down
        gevent.signal(signal.SIGQUIT, gevent.kill)
        if self.gth:
            self.gth.kill()  # just kill it for a seamless restart...

        self.gth = gevent.spawn(ftpd_block, address=self.address, authorizer=self.authorizer, root_path=self.root_path)
        return self.gth

    def stop(self):
        self.gth.kill()

if __name__ == '__main__':

    ftpd = None
    if len(sys.argv) == 2:
        ftpd = FTPTestServer(root_path=sys.argv[1])
    else:
        ftpd = FTPTestServer()
        if len(sys.argv) > 2:
            print("Usage: {0} <root_path>".format(sys.argv[0]))
            sys.exit(127)
    f = ftpd.start()

    # testing different shutdown flow
    attempt_proactive_stop = False  # change this as needed

    if attempt_proactive_stop:
        time.sleep(5)
        ftpd.stop()
    else:  # just wait to be killed (reactive stop)
        try:
            f.get()  # we block here, waiting on greenlet
            # Note that child process will receive any Keyboard interrupt,
            # so the process tree gets cleaned up properly from the bottom.
        except KeyboardInterrupt:
            pass  # because the future will also forward exceptions
