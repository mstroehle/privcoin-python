#!/usr/bin/env python

from setuptools import setup

VERSION = None
with open('privcoin/__init__.py') as f:
    for line in f:
        if line.startswith('__version__'):
            VERSION = line.replace("'", '').split('=')[1].strip()
            break
if VERSION is None:
    raise ValueError('__version__ not found in __init__.py')

DOWNLOAD_URL = 'https://github.com/teran-mckinney/privcoin-python/tarball/{}'

DESCRIPTION = 'privcoin.io Bitcoin Mixer Library'

setup(
    python_requires='>=3.3',
    name='privcoin',
    version=VERSION,
    author='Teran McKinney',
    author_email='sega01@go-beyond.org',
    description=DESCRIPTION,
    keywords=['bitcoin', 'bitcoincash', 'mixer', 'mixing'],
    license='Unlicense',
    url='https://github.com/teran-mckinney/privcoin-python',
    download_url=DOWNLOAD_URL.format(VERSION),
    packages=['privcoin'],
    install_requires=[
        'aaargh',
        'requests',
        'pyqrcode'
    ],
    entry_points={
        'console_scripts': [
            'privcoin = privcoin:main'
        ]
    }
)
