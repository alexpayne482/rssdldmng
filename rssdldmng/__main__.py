"""Start RSS Download Manager."""
# from __future__ import print_function

import argparse
import os
import sys
import errno
import logging

from rssdldmng.const import (
    __version__,
    REQUIRED_PYTHON_VER,
    CONFIG_DIR_NAME,
    DEFAULT_LOG_FILE
)

from rssdldmng.rssdldmng import RSSdldMng

_LOGGER = logging.getLogger(__name__)


def validate_python() -> None:
    """Validate that the right Python version is running."""
    if sys.version_info[:3] < REQUIRED_PYTHON_VER:
        print("RSSDld requires at least Python {}.{}.{}".format(*REQUIRED_PYTHON_VER))
        sys.exit(1)


def get_default_config_dir() -> str:
    """Put together the default configuration directory based on the OS."""
    data_dir = os.getenv('APPDATA') if os.name == "nt" else os.path.expanduser('~')
    return os.path.join(data_dir, CONFIG_DIR_NAME)


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
                except OSError as exc:  # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = argparse.ArgumentParser(
        description="RSS Downloader (RSSDld)")
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument(
        '-c', '--config',
        metavar='path_to_config_dir',
        default=get_default_config_dir(),
        help="Directory that contains the RSSDld configuration")
    parser.add_argument(
        '--debug',
        action='store_true',
        default=True,
        help='Start RSSDld in debug mode')
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        default=False,
        help="Enable verbose logging to file.")
    parser.add_argument(
        '--log-file',
        type=str,
        default='{}'.format(DEFAULT_LOG_FILE),
        help='Log file to write to. If not set, CONFIG/{} is used'.format(DEFAULT_LOG_FILE))

    arguments = parser.parse_args()
    return arguments


def main() -> int:
    """Start RSS downloader."""
    validate_python()
    args = get_arguments()

    # config
    config_dir = os.path.join(os.getcwd(), args.config)
    ensure_config_path(config_dir)

    # logging
    FORMAT = '%(asctime)-15s %(levelname)-7s %(name)-30s %(message)s'
    LEVEL = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format=FORMAT, level=logging.DEBUG if args.debug else logging.INFO)
    fh = logging.FileHandler(os.path.join(config_dir, args.log_file))
    fh.setLevel(LEVEL)
    fh.setFormatter(logging.Formatter(FORMAT))
    logging.getLogger('').addHandler(fh)

    # start main loop
    mng = RSSdldMng(config_dir)
    mng.run()

    # return
    return 0


if __name__ == "__main__":
    sys.exit(main())
