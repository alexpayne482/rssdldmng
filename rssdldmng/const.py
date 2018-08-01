import os
import sys

# Versioning
MAJOR_VERSION = 0
MINOR_VERSION = 3
PATCH_VERSION = '1'
__short_version__ = '{}.{}'.format(MAJOR_VERSION, MINOR_VERSION)
__version__ = '{}.{}'.format(__short_version__, PATCH_VERSION)

REQUIRED_PYTHON_VER = (3, 5, 2)

# default config
APPNAME = 'rssdldmng'
CONFIG_DIR_NAME = '.{}'.format(APPNAME)
CONFIG_FILE = 'configuration.json'
DEFAULT_LOG_FILE = '{}.log'.format(APPNAME)