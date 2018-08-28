#!/usr/bin/env python3
"""RSS Download Manager setup script."""
from datetime import datetime as dt
from setuptools import setup, find_packages

import rssdldmng.const as rssdld_const


PROJECT_NAME = 'RSS Download Manager'
PROJECT_PACKAGE_NAME = 'rssdldmng'
PROJECT_LICENSE = 'Apache License 2.0'
PROJECT_AUTHOR = 'Alexander Payne'
PROJECT_COPYRIGHT = ' 2018-{}, {}'.format(dt.now().year, PROJECT_AUTHOR)
PROJECT_URL = 'https://github.com/alexpayne482/rssdldmng'
PROJECT_EMAIL = 'alexander.payne.482@gmail.com'

PROJECT_GITHUB_USERNAME = 'alexpayne482'
PROJECT_GITHUB_REPOSITORY = 'rssdldmng'

PYPI_URL = 'https://pypi.python.org/pypi/{}'.format(PROJECT_PACKAGE_NAME)
GITHUB_PATH = '{}/{}'.format(
    PROJECT_GITHUB_USERNAME, PROJECT_GITHUB_REPOSITORY)
GITHUB_URL = 'https://github.com/{}'.format(GITHUB_PATH)

DOWNLOAD_URL = '{}/releases/download/{}-{}.zip'.format(
    GITHUB_URL, PROJECT_PACKAGE_NAME, rssdld_const.__version__)
PROJECT_URLS = {
    'Bug Reports': '{}/issues'.format(GITHUB_URL),
}

PACKAGES = find_packages(exclude=['tests', 'tests.*'])

with open('requirements.txt') as f:
    REQUIRES = [line.strip() for line in f if line.strip()]

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
