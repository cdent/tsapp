"""
Authentication routine to target server, to get
auth_token.
"""

import urllib2
import Cookie

from .http import http_write


def authenticate(config, user, password):
    """
    Authenticate the user with password against target_server,
    return the value of the tiddlyweb_user cookie.
    """

    post_data = dict(user=user, password=password)
    target = config['target_server']
    uri = target + '/challenge/tiddlywebplugins.tiddlyspace.cookie_form'

    # This will always error
    try:
        response, mime_type = http_write(method='POST',
                mime_type='application/x-www-form-urlencoded',
                uri=uri, data=post_data)
    except urllib2.HTTPError, exc:
        status = exc.getcode()
        if status < 400:
            cookie_data = exc.info().getheader('Set-Cookie')
            cookie = Cookie.SimpleCookie()
            cookie.load(cookie_data)
            auth_data = cookie['tiddlyweb_user'].value
        else:
            raise

    return auth_data
