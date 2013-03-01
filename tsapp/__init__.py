"""
Basic starting point for tsapp commands.
"""

from __future__ import absolute_import

import getpass
import glob
import os
import sys


__version__ = '0.3.4'


def error_exit(code, message=""):
    """
    Exit with code and provided message.
    """
    if message:
        sys.stderr.write("%s\n" % message)
    sys.exit(code)


def write_config(new_data):
    """
    Update the local .tsapp file with the provided new_data
    merged in.

    Note that this will remove any comments and change the
    order of the keys.
    """
    try:
        existing_data = _read_config('.')
    except IOError:
        existing_data = {}
    existing_data.update(new_data)

    _write_config(existing_data)


def _write_config(data):
    """
    Do the actual writing of one single config file.
    """
    def_umask = os.umask(0077)
    config_file = open('./.tsapp', 'w')

    for key, value in data.iteritems():
        key = key.strip()
        value = value.strip()
        config_file.write('%s:%s\n' % (key, value))

    config_file.close()
    os.umask(def_umask)


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
            new_data = _read_config(path)
            config.update(new_data)
        except IOError:
            pass
    return config


def _read_config(path):
    """
    Do the actual reading of one single config file.
    Return a dict of the contained info.
    """
    config = {}
    config_file = open(os.path.join(path, '.tsapp'))
    for line in config_file.readlines():
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        if key and value and not key.startswith('#'):
            config[key] = value
    return config


def delete_config_property(key):
    """
    Remove a line of config identified by it's key.
    """
    try:
        existing_data = _read_config('.')
    except IOError:
        existing_data = {}
    existing_data.pop(key)

    _write_config(existing_data)


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


def do_auth(args):
    """
    Authenticate the provided user against the target_server
    by putting them through the appropriate challenger.
    """
    from .auth import authenticate

    config = read_config()
    user = args[0]
    password = getpass.getpass(prompt='Password: ')

    auth_data = None

    try:
        auth_data = authenticate(config, user, password)
    except Exception, exc:
        sys.stderr.write('%s\n' % exc)
        sys.exit(1)

    write_config({'auth_token': auth_data})


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
    Push the assets or single tiddler to the target server, into target_bag.
    """
    _push(args, hard=False)


def push_hard(args):
    """
    Push the assets or single tiddler to the target server, into target_bag,
    deleting the assets first.
    """
    _push(args, hard=True)


def _push(args, hard=False):
    """
    Do the actual pushing.
    """
    from .push import push_assets

    config = read_config()
    auth_token = config.get('auth_token')

    target_server = config.get('target_server')
    target_bag = args[0]

    try:
        tiddler = args[1]
    except IndexError:
        tiddler = None

    if not '_' in target_bag:
        target_bag = '%s_public' % target_bag

    try:
        push_assets(target_server, target_bag, auth_token,
                tiddler=tiddler, hard=hard)
    except Exception, exc:
        sys.stderr.write('%s\n' % exc)
        sys.exit(1)


def delete(args):
    """
    Delete a single tiddler from the server at the named bag.

    tsapp delete bag_name tiddler_title
    """
    from .delete import delete_tiddler

    bag_name = args[0]
    tiddler_title = args[1]
    config = read_config()

    try:
        delete_tiddler(config, bag_name, tiddler_title)
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
    'push_hard': push_hard,
    'serve': run_server,
    'auth': do_auth,
    'delete': delete,
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
        error_exit(1, 'command or arg required')
    except KeyError, exc:
        error_exit(1, 'command unknown: %s' % exc)
    # let others raise themselves, for now
