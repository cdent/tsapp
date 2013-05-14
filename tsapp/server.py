"""
Start a web server to host the proxy.
"""

import sys

from .proxy import create_app
from cherrypy.wsgiserver import CherryPyWSGIServer


def start_server(config):
    """
    Make a server and start it up as a daemon.
    """
    port = int(config['port'])
    local_host = config['local_host']

    server = CherryPyWSGIServer((local_host, port), create_app(config))

    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
        sys.exit(0)
