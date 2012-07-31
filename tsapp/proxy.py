"""
WSGI app that provides a proxy to tiddlyspace as needed.
"""

from __future__ import absolute_import

import os
import mimetypes
import urllib2

from .http import http_write


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
    query_string = environ.get('QUERY_STRING')
    content_length = int(environ['CONTENT_LENGTH'])
    content_type = environ['CONTENT_TYPE']

    auth_token = config.get('auth_token')
    target_server = config.get('target_server')

    uri = target_server + path 
    if query_string:
        uri = uri + '?' + query_string
    try:
        response, mime_type = http_write(method=method, uri=uri,
                auth_token=auth_token, filehandle=environ['wsgi.input'],
                count=content_length, mime_type=content_type)
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

    query_string = environ.get('QUERY_STRING')

    path = environ['PATH_INFO']
    path = path.lstrip('/')
    path_parts = path.split('/')

    control_view = environ.get('HTTP_X_CONTROLVIEW')
    accept = environ.get('HTTP_ACCEPT')

    try:
        if len(path_parts) == 1:
            try:
                filehandle = open(path)
                mime_type = mimetypes.guess_type(path)[0]
            except IOError:
                filehandle = in_assets(path)
                mime_type = mimetypes.guess_type(path)[0]
        else:
            local_path = path_parts[-1]
            filehandle = in_assets(local_path)
            mime_type = mimetypes.guess_type(local_path)[0]
    except IOError:
        try:
            if query_string:
                path = path + '?' + query_string
            filehandle = at_server(target_server, path, accept,
                    auth_token, control_view)
            mime_type = filehandle.info().gettype()
        except IOError, exc:
            try:
                code = exc.getcode()
            except AttributeError:
                raise exc
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


def at_server(server, path, accept, auth_token, control_view):
    """
    Filehandle for the resource at the target server.
    """
    if not path.startswith('/'):
        path = '/%s' % path
    req = urllib2.Request(server + path)
    if accept:
        req.add_header('Accept', accept)
    if auth_token:
        req.add_header('Cookie', 'tiddlyweb_user=%s' % auth_token)
    if control_view:
        req.add_header('X-ControlView', 'false')
    return urllib2.urlopen(req)
