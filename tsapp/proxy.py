"""
WSGI app that provides a proxy to tiddlyspace as needed.
"""

import os
import mimetypes
import urllib2


class NoRedirect(urllib2.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
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

    def __init__(self, auth_token=None):
        self.auth_token = auth_token

    def __call__(self, environ, start_response):
        method = environ['REQUEST_METHOD'].upper()
        if method != 'GET':
            return handle_write(environ, start_response, method, self.auth_token)
        else:
            return handle_get(environ, start_response, self.auth_token)


def handle_write(environ, start_response, method, auth_token):
    """
    Handle a POST, PUT or DELETE.
    """
    path = environ['PATH_INFO']
    content_length = environ['CONTENT_LENGTH']

    opener = urllib2.build_opener(NoRedirect())

    req = urllib2.Request('http://tiddlyspace.com' + path)

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

    start_response('204 OK', [])
    content = response.read()
    return content


def handle_get(environ, start_response, auth_token):
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
                filehandle = at_server(path, auth_token)
                mime_type = filehandle.info().gettype()
            except IOError, exc:
                code = exc.getcode()
                start_response(str(code) + ' error', [])
                return []

    start_response('200 OK', [('Content-Type', mime_type)])
    return filehandle


def in_assets(path):
    return open(os.path.join('.', 'assets', path))

def at_server(path, auth_token):
    if not path.startswith('/'):
        path = '/%s' % path
    req = urllib2.Request('http://tiddlyspace.com' + path)
    if auth_token:
        req.add_header('Cookie', 'tiddlyweb_user=%s' % auth_token)
    return urllib2.urlopen(req)
