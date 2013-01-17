"""
HTTP fundamentals.
"""

import mimetypes
import sys
import urllib2
import urllib


mimetypes.add_type('text/plain', '.tid')
mimetypes.add_type('application/x-woff', '.woff')


class NoRedirect(urllib2.HTTPRedirectHandler):
    """
    Handler for urllib2 that avoids following redirects.
    """
    def redirect_request(self, req, fproxy, code, msg, hdrs, newurl):
        pass


def http_write(method='PUT', uri=None, auth_token=None, filehandle=None,
        filename=None, mime_type=None, data=None, count=None):
    """
    Do an HTTP write method. As you can see from the method
    signature this is attempting to generalize a lot of different
    ways of being called. Which is dumb, but it is working for now.
    """
    opener = urllib2.build_opener(NoRedirect())

    if filename and method is not 'DELETE':
        filehandle = open(filename)
        mime_type = mimetypes.guess_type(filename)[0]
        if not mime_type:
            sys.stderr.write('Unable to guess mime type for %s, skipping!\n'
                    % filename)
            return None, None

    req = urllib2.Request(uri.encode('utf-8'))

    if auth_token:
        req.add_header('Cookie', 'tiddlyweb_user=%s' % auth_token)

    if method is not 'DELETE':
        req.add_header('Content-Type', mime_type)

    req.get_method = lambda: method
    if count:
        req.add_data(filehandle.read(count))
    elif filehandle:
        req.add_data(filehandle.read())
    elif data:
        data = urllib.urlencode(data)
        req.add_data(data)

    try:
        response = opener.open(req)
    except urllib2.HTTPError, exc:
        sys.stderr.write('WARN: %s response for %s %s\n' % (exc, method, uri))
        return None, None

    mime_type = response.info().gettype()
    return response, mime_type
