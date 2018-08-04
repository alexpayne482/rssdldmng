#!/usr/bin/env python3
"""RSS Download Manager setup script."""
from datetime import datetime as dt
from setuptools import setup, find_packages

import rssdldmng.const as rssdld_const


PROJECT_NAME = 'RSS Download Manager'
PROJECT_PACKAGE_NAME = 'rssdldmng'
PROJECT_LICENSE = 'Apache License 2.0'
PROJECT_AUTHOR = 'Liviu'
PROJECT_COPYRIGHT = ' 2018-{}, {}'.format(dt.now().year, PROJECT_AUTHOR)
PROJECT_URL = ''
PROJECT_EMAIL = ''

PROJECT_GITHUB_USERNAME = 'liviuflore'
PROJECT_GITHUB_REPOSITORY = 'rssdldmng'

PYPI_URL = 'https://pypi.python.org/pypi/{}'.format(PROJECT_PACKAGE_NAME)
GITHUB_PATH = '{}/{}'.format(
    PROJECT_GITHUB_USERNAME, PROJECT_GITHUB_REPOSITORY)
GITHUB_URL = 'https://github.com/{}'.format(GITHUB_PATH)

DOWNLOAD_URL = '{}/archive/{}.zip'.format(GITHUB_URL, rssdld_const.__version__)
PROJECT_URLS = {
    'Bug Reports': '{}/issues'.format(GITHUB_URL),
}

PACKAGES = find_packages(exclude=['tests', 'tests.*'])

REQUIRES = [
    'kodipydent>=0.3.1',
    'pip>=8.0.3',
    'requests==2.19.1',
    'feedparser>=5.2.1',
    'pysqlite3==0.2.0',
    'trakt==2.8.0'
]

MIN_PY_VERSION = '.'.join(map(str, rssdld_const.REQUIRED_PYTHON_VER))

setup(
    name=PROJECT_PACKAGE_NAME,
    version=rssdld_const.__version__,
    url=PROJECT_URL,
    download_url=DOWNLOAD_URL,
    project_urls=PROJECT_URLS,
    author=PROJECT_AUTHOR,
    author_email=PROJECT_EMAIL,
    packages=PACKAGES,
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    python_requires='>={}'.format(MIN_PY_VERSION),
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'rssdldmng = rssdldmng.__main__:main'
        ]
    },
)
