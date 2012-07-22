"""
Basic starting point for tsapp commands.
"""

import sys, os

def error_exit(code, message=""):
    """
    Exit with code and provided message.
    """
    if message:
        sys.stderr.write("%s\n" % message)
    sys.exit(code)


def read_config():
    """
    Read the local config to manage options.

    TODO: Get local overrides for things like target server.
    """
    homedir = os.getenv('HOME')
    config = {}
    if homedir:
        try:
            config_file = open(os.path.join(homedir, '.tsapp'))
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
    Run a wsgi server at :8080 which will look locally for content
    and if not found there, look remotely. A path which takes the
    form /bags/something/tiddlers/filename will look in the local
    dir called "assets" for "filename". If the file is not found, the
    full path will be looked up at tiddlyspace.com.
    
    If the path is a single file or begins with "/" then the file
    will be looked for in the local dir without failover to the
    remote server.

    At the moment only GET is handled. PUT is recognized, but not
    yet proxied. When it is implemented it will only proxy, no
    local handing will be done.
    """
    config = read_config()

    from wsgiref.simple_server import make_server
    from tsapp.proxy import create_app

    httpd = make_server('', 8080, create_app(config['auth_token']))

    print "Serving on http://0.0.0.0:8080/index.html"

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)


def show_help(args):
    """
    Display this help.
    """
    for command in COMMANDS:
        print '%s%s' % (command, COMMANDS[command].__doc__)


COMMANDS = {
        'serve': run_server,
        'help': show_help
        }

def handle(args):
    """
    Process command line arguments to call commands.
    """
    try:
        command = args.pop(0)
        functor = COMMANDS[command]
        functor(args)
    except IndexError:
        error_exit(1, "command required")
    except KeyError:
        error_exit(1, "command unknown")
    # let others raise themselves, for now
