from setuptools import setup, find_packages

from tsapp import __version__ as VERSION

setup(
    name = 'tsapp',
    version = VERSION,
    description = 'Manage an app for TiddlySpace.',
    author = 'Chris Dent',
    author_email = 'cdent@peermore.com',
    url = 'http://pypi.python.org/pypi/tsapp',
    platforms = 'Posix; MacOS X; Windows',
    scripts = ['script/tsapp'],
    packages = find_packages(exclude=['test']),
    include_package_data = True,
    zip_safe = False
    )
