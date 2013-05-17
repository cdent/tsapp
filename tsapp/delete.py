"""
Do a single delete tiddler operation.
"""

from urllib import quote

from .http import http_write


def delete_tiddler(config, bag_name, tiddler_title):
    """
    Delete the tiddler named by tiddler_title from bag_name
    at target_server.
    """

    target_server = config['target_server']
    server_prefix = config.get('server_prefix')
    auth_token = config.get('auth_token')
    uri = 'bags/%s/tiddlers/%s' % (quote(bag_name, safe=''),
            quote(tiddler_title, safe=''))
    if server_prefix:
        uri = '%s/%s' % (server_prefix, uri)
    uri = '%s/%s' % (target_server, uri)

    http_write(method='DELETE', uri=uri, auth_token=auth_token)
