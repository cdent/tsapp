"""
HTTP fundamentals.
"""

import mimetypes
import urllib2
import urllib


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

    if filename:
        filehandle = open(filename)
        mime_type = mimetypes.guess_type(filename)[0]

    req = urllib2.Request(uri)

    if auth_token:
        req.add_header('Cookie', 'tiddlyweb_user=%s' % auth_token)

    try:
        req.add_header('Content-Type', mime_type)
    except KeyError:
        pass

    req.get_method = lambda: method
    if count:
        req.add_data(filehandle.read(count))
    elif filehandle:
        req.add_data(filehandle.read())
    else:
        data = urllib.urlencode(data)
        req.add_data(data)

    response = opener.open(req)
    mime_type = response.info().gettype()
    return response, mime_type
