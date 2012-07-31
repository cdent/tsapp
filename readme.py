"""
Build the readme by pulling in content from remote.
"""

import requests

from urllib import quote

TEMPLATE = 'README.template'
OUTPUT = 'README'
TIDDLER_SOURCE = 'http://tsapp.tiddlyspace.com/bags/tsapp_public/tiddlers/'

def build():
    template_file = open(TEMPLATE)
    output_file = open(OUTPUT, 'w')

    for line in template_file:
        if line.startswith('ink:'):
            tiddler = line.split(':', 1)[1].strip()
            tiddler_text = get_tiddler(tiddler)
            output_file.write(tiddler_text)
        else:
            output_file.write(line)


def get_tiddler(tiddler):
    uri = TIDDLER_SOURCE + quote(tiddler, safe='') + '.txt'
    response = requests.get(uri)
    return response.text.split('\n\n', 1)[1]

if __name__ == '__main__':
    build()
