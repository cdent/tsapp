"""
WSGI app that provides a proxy to tiddlyspace as needed.
"""

import os
import mimetypes
import urllib2


def app(environ, start_response):
    if environ['REQUEST_METHOD'].upper() == 'PUT':
        return handle_put(environ, start_response)
    else:
        return handle_get(environ, start_response)

def handle_put(environ, start_response):
    pass

def handle_get(environ, start_response):
    path = environ['PATH_INFO']

    path = path.lstrip('/')
    path_parts = path.split('/')

    if len(path_parts) == 1:
        try:
            filehandle = open(path)
            mime_type = mimetypes.guess_type(path)[0]
        except IOError:
            start_response('404 Not Found', [])
            return []
    else:
        local_path = path_parts[-1]
        try:
            filehandle = in_assets(local_path)
            mime_type = mimetypes.guess_type(local_path)[0]
        except IOError:
            try:
                filehandle = at_server(path)
                mime_type = filehandle.info().gettype()
            except IOError, exc:
                code = exc.getcode()
                start_response(str(code) + ' error', [])
                return []

    start_response('200 OK', [('Content-Type', mime_type)])
    return filehandle


def in_assets(path):
    return open(os.path.join('.', 'assets', path))

def at_server(path):
    if not path.startswith('/'):
        path = '/%s' % path
    return urllib2.urlopen('http://tiddlyspace.com' + path)

