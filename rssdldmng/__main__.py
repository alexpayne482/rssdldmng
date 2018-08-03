"""Start RSS Download Manager."""
#from __future__ import print_function

import argparse
import os
import platform
import sys
import logging

import rssdldmng.config as config_util

from rssdldmng.const import (
    __version__,
    REQUIRED_PYTHON_VER,
    CONFIG_DIR_NAME,
    CONFIG_FILE,
    DEFAULT_LOG_FILE
)

from rssdldmng.rssdldmng import RSSdldMng


_LOGGER = logging.getLogger(__name__)

def validate_python() -> None:
    """Validate that the right Python version is running."""
    if sys.version_info[:3] < REQUIRED_PYTHON_VER:
        print("RSSDld requires at least Python {}.{}.{}".format(*REQUIRED_PYTHON_VER))
        sys.exit(1)

g_config_dir = None
def run_rssdld(config_dir: str, args: argparse.Namespace) -> int:
    """Run rssdld manager"""
    config_util.ensure_config_file(config_dir)
    _LOGGER.info('Config directory: {0}'.format(config_dir))
    
    global g_config_dir
    g_config_dir = config_dir
    #config = config_util.load_config_file(config_dir)
    #config['dbpath'] = os.path.join(config_dir, 'shows.db')
    #config['debug'] = args.debug
    #config['cfgdir'] = config_dir
    mng = RSSdldMng(config_dir)

    return mng.run()


def save_config(config):
    if g_config_dir:
        config_util.save_config_file(config, g_config_dir)


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = argparse.ArgumentParser(
        description="RSS Downloader (RSSDld)")
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument(
        '-c', '--config',
        metavar='path_to_config_dir',
        default=config_util.get_default_config_dir(),
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
    config_util.ensure_config_path(config_dir)

    # logging
    FORMAT = '%(asctime)-15s %(levelname)-7s %(name)-30s %(message)s'
    LEVEL = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format=FORMAT, level=logging.DEBUG if args.debug else logging.INFO)
    fh = logging.FileHandler(os.path.join(config_dir, args.log_file))
    fh.setLevel(LEVEL)
    fh.setFormatter(logging.Formatter(FORMAT))
    logging.getLogger('').addHandler(fh)

    # start main loop
    run_rssdld(config_dir, args)

    # return
    return 0


if __name__ == "__main__":
    sys.exit(main())
