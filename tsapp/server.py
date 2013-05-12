"""
Start a web server to host the proxy.
"""

import sys

from .proxy import create_app
from wsgiref.simple_server import make_server

def start_server(config):
    """
    Make a server and start it up as a daemon.
    """
    port = int(config['port'])
    local_host = config['local_host']

    httpd = make_server(local_host, port, create_app(config))

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
