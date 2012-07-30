"""
Basic starting point for tsapp commands.
"""

from __future__ import absolute_import

import glob
import os
import sys


def error_exit(code, message=""):
    """
    Exit with code and provided message.
    """
    if message:
        sys.stderr.write("%s\n" % message)
    sys.exit(code)


def read_config():
    """
    Read the local config to manage options. There can be
    a .tsapp file in the local dir or in the users HOME dir.
    The HOME dir is read first, and then the local file overrides
    that.
    """
    homedir = os.getenv('HOME')
    # defaults
    config = {
        'target_server': 'http://tiddlyspace.com',
        'local_host': '0.0.0.0',
        'port': 8080,
    }

    paths = ['.']
    if homedir:
        paths.insert(0, homedir)
    for path in paths:
        try:
            config_file = open(os.path.join(path, '.tsapp'))
            for line in config_file.readlines():
                key, value = line.split(':', 1)
                key = key.rstrip().lstrip()
                value = value.rstrip().lstrip()
                if key and value and not key.startswith('#'):
                    config[key] = value
        except IOError:
            pass
    return config


def run_server(args):
    """
    Run a wsgi server which will look locally for content
    and if not found there, look remotely. A path which takes the
    form /bags/something/tiddlers/filename will look in the local
    dir called "assets" for "filename". If the file is not found, the
    full path will be looked up at tiddlyspace.com.

    If the path is a single file or begins with "/" then the file
    will be looked for in the local dir without failover to the
    remote server.

    GET is handled locally and proxied. Other methods (write)
    only proxy.
    """
    config = read_config()

    from wsgiref.simple_server import make_server
    from .proxy import create_app

    port = int(config['port'])
    local_host = config['local_host']

    httpd = make_server(local_host, port, create_app(config))

    uri = 'http://%s:%s/' % (local_host, port)

    print 'Serving %s' % uri
    for html in glob.glob('*.html'):
        print 'Try: %s%s' % (uri, html)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)


def new_app(args):
    """
    Create the directory and stub files for a new app.

    Which means:

    * make a directory
    * put a stub index.html
    * make an assets directory
    * local .tsapp
    """
    from .instance import make_instance

    target = args[0]

    try:
        make_instance(target)
    except Exception, exc:
        sys.stderr.write('%s\n' % exc)
        sys.exit(1)


def push(args):
    """
    Push the assets to the target server, into target_bag.
    """
    from .push import push_assets

    config = read_config()
    auth_token = config.get('auth_token')

    target_server = config.get('target_server')
    target_bag = args[0]

    if not (target_bag.endswith('_public')
            or target_bag.endswith('_private')):
        target_bag = '%s_public' % target_bag

    try:
        push_assets(target_server, target_bag, auth_token)
    except Exception, exc:
        sys.stderr.write('%s\n' % exc)
        sys.exit(1)


def show_help(args):
    """
    Display this help.
    """
    for command in COMMANDS:
        print '%s%s' % (command, COMMANDS[command].__doc__)


COMMANDS = {
    'help': show_help,
    'init': new_app,
    'push': push,
    'serve': run_server,
}


def handle(args):
    """
    Process command line arguments to call commands.
    """
    try:
        command = args.pop(0)
        functor = COMMANDS[command]
        functor(args)
    except IndexError, exc:
        error_exit(1, 'command required')
    except KeyError, exc:
        error_exit(1, 'command unknown: %s' % exc)
    # let others raise themselves, for now
