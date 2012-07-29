"""
Create the app's instance dir.
"""

import os
import shutil

from pkg_resources import resource_filename

STUB_HTML = resource_filename('tsapp', 'resources/stub.html')


def make_instance(target):
    """
    Create a new app instance dir.
    """
    if os.sep in target:
        raise IOError('%s not allowed in target' % os.sep)

    # these will OSError if the dirs exist
    os.mkdir(target)
    os.mkdir(os.path.join(target, 'assets'))

    shutil.copyfile(STUB_HTML, os.path.join(target, 'index.html'))
