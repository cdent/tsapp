"""
WSGI app that provides a proxy to tiddlyspace as needed.
"""

import os
import mimetypes
import urllib2


class NoRedirect(urllib2.HTTPRedirectHandler):
    """
    Handler for urllib2 that avoids following redirects.
    """
    def redirect_request(self, req, fproxy, code, msg, hdrs, newurl):
        pass


def create_app(auth_token=None):
    """
    Return the app, configured with proper auth token.
    """
    return App(auth_token)


class App(object):
    """
    Wrap the proxy application as a class so we can pass in
    auth token easily.
    """

    def __init__(self, config):
        self.config = config

    def __call__(self, environ, start_response):
        method = environ['REQUEST_METHOD'].upper()
        if method != 'GET':
            return handle_write(environ, start_response, method, self.config)
        else:
            return handle_get(environ, start_response, self.config)


def handle_write(environ, start_response, method, config):
    """
    Handle a POST, PUT or DELETE.
    """
    path = environ['PATH_INFO']
    content_length = environ['CONTENT_LENGTH']

    auth_token = config.get('auth_token')
    target_server = config.get('target_server')

    opener = urllib2.build_opener(NoRedirect())

    req = urllib2.Request(target_server + path)

    if auth_token:
        req.add_header('Cookie', 'tiddlyweb_user=%s' % auth_token)

    try:
        req.add_header('Content-Type', environ['CONTENT-TYPE'])
    except KeyError:
        pass

    req.get_method = lambda: method
    req.add_data(environ['wsgi.input'].read(int(content_length)))

    try:
        response = opener.open(req)
        mime_type = response.info().gettype()
    except IOError, exc:
        code = exc.getcode()
        start_response(str(code) + ' error', [])
        return ['%s' % exc]

    start_response('204 OK', [('Content-type', mime_type)])
    content = response.read()
    return content


def handle_get(environ, start_response, config):
    """
    Proxy a GET request. Look in the local dir and the assets
    dir. If not there try at the target server, at the path
    requested.
    """

    auth_token = config.get('auth_token')
    target_server = config.get('target_server')

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
                filehandle = at_server(target_server, path, auth_token)
                mime_type = filehandle.info().gettype()
            except IOError, exc:
                code = exc.getcode()
                start_response(str(code) + ' error', [])
                return []

    start_response('200 OK', [('Content-Type', mime_type)])
    return filehandle


def in_assets(path):
    """
    Open the requested path in the assets directory.
    If the file is not present, an error will cause
    a failover to the target server.
    """
    return open(os.path.join('.', 'assets', path))


def at_server(server, path, auth_token):
    """
    Filehandle for the resource at the target server.
    """
    if not path.startswith('/'):
        path = '/%s' % path
    req = urllib2.Request(server + path)
    if auth_token:
        req.add_header('Cookie', 'tiddlyweb_user=%s' % auth_token)
    return urllib2.urlopen(req)
