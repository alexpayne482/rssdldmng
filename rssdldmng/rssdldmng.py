import os
import sys
import logging
import time
import json
from datetime import datetime

from rssdldmng.rssdld.downloader import Downloader
from rssdldmng.rssdld.episode import IState
from rssdldmng.api.server import ApiServer
from rssdldmng.const import (
    __version__,
    CONFIG_FILE,
    DB_FILE,
    API_PORT
)
from rssdldmng.config import (
    Config,
    JsonConvert
)

log = logging.getLogger(__name__)


class RSSdldMng:

    def __init__(self, config_dir):
        """Initialize new RSS Download Manager object."""
        log.info('Starting RDM version {0}'.format(__version__))
        log.info('Config directory: {0}'.format(config_dir))

        self.config_dir = os.path.abspath(config_dir)

        self.config_file = os.path.join(self.config_dir, CONFIG_FILE)
        self.db_file = os.path.join(self.config_dir, DB_FILE)

        self.config = self.load_config(self.config_file)
        self.set_logging(self.config.logging)
        self.downloader = None
        self.http_server = None

    def load_config(self, config_file):
        if not os.path.isfile(config_file):
            log.warning("Unable to find configuration. Creating default ({0})".format(config_file))
            return JsonConvert.ToFile(Config(), config_file)
        try:
            return JsonConvert.FromFile(config_file)
        except IOError:
            log.error("Fatal Error: Unable to read configuration file {0}".format(config_file))
            sys.exit(1)

    def save_config(self):
        try:
            JsonConvert.ToFile(self.config, self.config_file)
        except IOError:
            log.error("Unable to save configuration file {0}".format(self.config_file))
        return

    def set_logging(self, lconfig=None):
        if not lconfig:
            return

        if lconfig.level == 'error':
            logging.getLogger().setLevel(logging.ERROR)
        elif lconfig.level == 'warning':
            logging.getLogger().setLevel(logging.WARNING)
        elif lconfig.level == 'info':
            logging.getLogger().setLevel(logging.INFO)
        elif lconfig.level == 'debug':
            logging.getLogger().setLevel(logging.DEBUG)

    def run(self):
        try:
            log.debug("Starting RDM core loop")

            self.downloader = Downloader(self.db_file, self.config.downloader)
            self.downloader.start()

            self.http_server = ApiServer(self.config.apiport, self)
            self.http_server.start()

            # infinite sleep
            while True:
                time.sleep(10)
                if self.downloader.is_stopped():
                    break

        except KeyboardInterrupt:
            log.debug("RDM core loop interrupted")
        finally:
            log.debug("Stopping RDM core loop")
            if self.http_server:
                self.http_server.stop()
            if self.downloader:
                self.downloader.stop()

    # API actions
    def dump_db_items(self):
        if self.downloader:
            self.downloader.dumpDB()
            for ep in self.downloader.getEpisodesFull(published=(int(datetime.now().timestamp()) - 86400 * 7)):
                log.info("{:<24s} S{:02d}E{:02d} {:12s} {:s} {:4d}% {:s}".format(
                    ep.showname, ep.season, ep.episode, IState(ep.state).name, ep.title,
                    ep.torrent.progress if ep.torrent else -1, ep.library.dateadded if ep.library else 'none'))

    def get_latest(self, days=7):
        if self.downloader:
            return self.downloader.getEpisodesFull(published=(int(datetime.now().timestamp()) - 86400 * days))
        return []

    def get_status(self, days=7):
        new = 0
        downloading = 0
        available = 0
        if self.downloader:
            for ep in self.downloader.getEpisodesFull(published=(int(datetime.now().timestamp()) - 86400 * days)):
                if ep.state <= IState.NEW.value:
                    new += 1
                elif ep.state < IState.AVAILABLE.value:
                    downloading += 1
                else:
                    if not ep.library:
                        downloading += 1
                    elif ep.library.playcount < 1:
                        available += 1
            # return "{0} new, {1} downloading, {2} available".format(new, downloading, available)
            return {"new": new, "downloading": downloading, "available": available}
        return "NA"

