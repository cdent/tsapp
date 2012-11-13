"""
WSGI app that provides a proxy to tiddlyspace as needed.
"""

from __future__ import absolute_import

import os
import mimetypes
import sys
import urllib2
import uuid
from re import sub

from .http import http_write

from tsapp import write_config, read_config, delete_config_property
from tsapp.auth import authenticate

mimetypes.add_type('text/cache-manifest', '.appcache')


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
        # Always re-read the config as the auth token may be written/removed during a login/logout request.
        self.config = read_config()
        method = environ['REQUEST_METHOD'].upper()
        if method != 'GET':
            return handle_write(environ, start_response, method, self.config)
        else:
            return handle_get(environ, start_response, self.config)


def path_info_fixer(path):
    """
    So, like so many other web servers, wsgiref simple server
    chooses to unquote PATH_INFO before setting it in the
    WSGI environ. This means the path `/foo/bar%2fbaz%20zoom`
    becomes `/foo/bar/bar zoom` which is now impossible to
    return to its original form or to extract the correct, um,
    path info from.

    We can work around this in a known set of URIs, like tiddlyweb's
    api. Everywhere we expect a /, turn it into a uuid. All
    the other slashes turn back into %2F, then turn the uuid back
    into /.

    This is probably more complicated than it needs to be but
    I lost my brain somewhere along the way. I can't believe this
    sort of stuff still goes on in HTTP servers. Don't mess
    with the %2F!!!
    """
    token = str(uuid.uuid4())
    path = sub('^/', token, path, count=1)
    path = sub('(bags|recipes|tiddlers|revisions)/', '\g<1>' + token, path)
    path = sub('/(tiddlers|revisions)', token + '\g<1>', path)
    path = sub('/', '%2f', path)
    path = sub(token, '/', path)
    return path


def handle_write(environ, start_response, method, config):
    """
    Handle a POST, PUT or DELETE.
    """
    path = path_info_fixer(urllib2.quote(environ['PATH_INFO']))
    query_string = environ.get('QUERY_STRING')
    try:
        content_length = int(environ['CONTENT_LENGTH'])
        filehandle = environ['wsgi.input']
    except (KeyError, ValueError):
        content_length = None
        filehandle = None
    content_type = environ['CONTENT_TYPE']

    # ensure we don't try to read the input socket on a DELETE
    if method == 'DELETE':
        content_length = None
        filehandle = None

    auth_token = config.get('auth_token')
    target_server = config.get('target_server')

    # Intercept any login attempts and use the authenticate method if no auth token is present
    if path == '/challenge%2ftiddlywebplugins.tiddlyspace.cookie_form':
        if auth_token is None:
            form_data = environ['wsgi.input'].read(int(content_length)).split('&')
            user = form_data[0].split('=')[1]
            password = form_data[1].split('=')[1]
            try:
                auth_data = authenticate(config, user, password)
            except Exception, exc:
                sys.stderr.write('%s\n' % exc)
                status = exc.getcode()
                if status == 401:
                    start_response('401 Unauthorized', [('Content-type', 'text/plain')])
                    return []
                sys.exit(1)

            write_config({'auth_token': auth_data})

        start_response('204 OK', [('Content-type', 'text/plain')])
        return []

    # Intercept any logout attempts and remove the auth_token
    if path == '/logout':
        if auth_token is not None:
            delete_config_property('auth_token')

        start_response('204 OK', [('Content-type', 'text/plain')])
        return []

    uri = target_server + path
    if query_string:
        uri = uri + '?' + query_string
    try:
        response, mime_type = http_write(method=method, uri=uri,
                auth_token=auth_token, filehandle=filehandle,
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
        elif len(path_parts) == 4:
            local_path = path_parts[-1]
            filehandle = in_assets(local_path)
            mime_type = mimetypes.guess_type(local_path)[0]
        else:
            raise IOError('path wrong length')
    except IOError:
        try:
            path = path_info_fixer(urllib2.quote(path))
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
            return ['%s' % exc]

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