"""Module to help with parsing and generating configuration files."""
import logging
import os
import sys
import re
import shutil
import json

from rssdldmng.const import (
    CONFIG_DIR_NAME,
    CONFIG_FILE,
)

_LOGGER = logging.getLogger(__name__)

# default config
def_config = {
    "feed_poll_interval": 300,
    "lib_update_interval": 60,
    "feeds": [
        {
            "uri" : "http://showrss.info/other/all.rss",
            "download_dir" : "/media/Media/Series/{seriesname}/Season{seasonno:02}/",
            "filters": {
                "seriesname": ["Elementary"],
                "quality": ["720p"]
            }
        }
    ],
    "transmission": {
        "host": 'localhost',
        "port": 9091,
        "username": "user",
        "password": "pass"
    },
    "kodi": {
        "host": 'localhost',
        "port": 8080,
        "username": "user",
        "password": "pass"
    }
}

def ensure_config_path(config_dir: str) -> None:
    """Validate the configuration directory."""
    if not os.path.isdir(config_dir):
        if config_dir != get_default_config_dir():
            _LOGGER.error("Fatal Error: Specified configuration directory does not exist {}".format(config_dir))
            sys.exit(1)
        else:
            if not os.path.exists(config_dir):
                try:
                    os.makedirs(config_dir)
                except OSError as exc: # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise


def get_default_config_dir() -> str:
    """Put together the default configuration directory based on the OS."""
    data_dir = os.getenv('APPDATA') if os.name == "nt" else os.path.expanduser('~')
    return os.path.join(data_dir, CONFIG_DIR_NAME)


def find_config_file(config_dir: str) -> str:
    """Look in given directory for supported configuration files."""
    if config_dir is None:
        return None
    config_path = os.path.join(config_dir, CONFIG_FILE)
    return config_path if os.path.isfile(config_path) else None


def create_default_config(config_dir: str, detect_location: bool = True) -> str:
    """Create a default configuration file in given configuration directory.
    Return path to new config file if success, None if failed.
    This method needs to run in an executor.
    """
    config_path = os.path.join(config_dir, CONFIG_FILE)

    try:
        if not os.path.exists(os.path.dirname(config_path)):
            try:
                os.makedirs(os.path.dirname(config_path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        with open(config_path, 'wt') as config_file:
            config_file.write(json.dumps(def_config, sort_keys=True, indent=4))
        return config_path

    except IOError:
        _LOGGER.error("Unable to create default configuration file {0}".format(config_path))
        return None


def load_config_file(config_dir: str):
    config_path = os.path.join(config_dir, CONFIG_FILE)
    #_LOGGER.debug("load_config_file {0}".format(config_path))
    try:
        return json.loads(open(config_path).read())
    
    except IOError:
        _LOGGER.error("Unable to read configuration file {0}".format(config_path))
        return None


def save_config_file(config, config_dir):
    config_path = os.path.join(config_dir, CONFIG_FILE)
    #_LOGGER.debug("save_config_file {0}".format(config_path))
    try:
        with open(config_path, 'wt') as config_file:
            config_file.write(json.dumps(config, sort_keys=True, indent=4))
    except IOError:
        _LOGGER.error("Unable to save configuration file {0}".format(config_path))
    return


def ensure_config_file(config_dir: str) -> str:
    """Ensure configuration file exists."""
    config_path = find_config_file(config_dir)

    if config_path is None:
        _LOGGER.warning("Unable to find configuration. Creating default one in {0}".format(config_dir))
        config_path = create_default_config(config_dir)

    if config_path is None:
        _LOGGER.error('Error getting configuration path')
        sys.exit(1)

    return config_path

