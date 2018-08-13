import os
import sys
import logging
import math
import time
import re
import json
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)


from rssdldmng.rssdld.downloader import RSSdld
from rssdldmng.rssdld.episode import IState
from rssdldmng.rssdldapi import RSSdldApiServer
from rssdldmng.const import (
    CONFIG_FILE,
    DB_FILE,
    API_PORT
)

# default config
def_config = {
    "feeds": ["http://showrss.info/other/all.rss"],
    "apiport": API_PORT,
    "downloader": {
        "dir": "/media/Media/Series/{seriesname}/Season{seasonno:02}/",
        "series": ["Elementary"],
        "quality": ["720p"],
        "feed_poll_interval": 300,
        "lib_update_interval": 60,
    },
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

class RSSdldMng:

    def __init__(self, config_dir):
        """Initialize new RSS Download Manager object."""
        _LOGGER.info('Config directory: {0}'.format(config_dir))

        self.config_dir = os.path.abspath(config_dir)

        self.config_file = os.path.join(self.config_dir, CONFIG_FILE)
        self.db_file = os.path.join(self.config_dir, DB_FILE)

        self.config = self.load_config()
        self.downloader = None
        self.http_server = None


    def load_config(self):
        if not os.path.isfile(self.config_file):
            _LOGGER.warning("Unable to find configuration. Creating default one in {0}".format(self.config_dir))
            with open(self.config_file, 'wt') as file:
                file.write(json.dumps(def_config, sort_keys=True, indent=4))
        try:
            return json.loads(open(self.config_file).read())
        except IOError:
            _LOGGER.error("Fatal Error: Unable to read configuration file {0}".format(self.config_file))
            sys.exit(1)


    def save_config(self, config):
        try:
            with open(self.config_file, 'wt') as file:
                file.write(json.dumps(config, sort_keys=True, indent=4))
        except IOError:
            _LOGGER.error("Unable to save configuration file {0}".format(self.config_file))
        return


    def run(self):
        try:
            _LOGGER.debug("Starting RSSDld core loop")

            self.downloader = RSSdld(self.db_file, self.config)
            self.downloader.start()

            self.http_server = RSSdldApiServer(self.config.get('apiport', API_PORT), self)
            self.http_server.start()

            # infinite sleep
            while True:
                time.sleep(10)
                if self.downloader.is_stopped():
                    break

        except KeyboardInterrupt:
            _LOGGER.debug("RSSDld core loop interrupted")
        finally:
            _LOGGER.debug("Stopping RSSDld core loop")

            self.http_server.stop()
            self.downloader.stop()


    def get_latest(self, days=7):
        if self.downloader:
            return self.downloader.getDBitems(published = (int(datetime.now().timestamp()) - 86400 * days))
        return []

    def get_series(self):
        if self.downloader:
            return self.downloader.getSeries(True)
        return []

    def get_status(self, days):
        new = 0
        downloading = 0
        available = 0
        if self.downloader:
            for ep in self.downloader.getDBitems(published = (int(datetime.now().timestamp()) - 86400 * days)):
                if ep.state <= IState.NEW.value:
                    new += 1
                elif ep.state < IState.AVAILABLE.value:
                    downloading += 1
                else:
                    if not ep.library:
                        downloading += 1
                    elif ep.library.playcount < 1:
                        available += 1
            #return "{0} new, {1} downloading, {2} available".format(new, downloading, available)
            return { "new": new, "downloading" : downloading, "available": available }
        return "NA"


    def dump_db_items(self):
        if self.downloader:
            self.downloader.dumpDB()
            for ep in self.downloader.getDBitems(published = (int(datetime.now().timestamp()) - 86400 * 7)):
                _LOGGER.info("{:<24s} S{:02d}E{:02d} {:12s} {:s} {:4d}% {:s}".format(ep.showname, ep.season, ep.episode, 
                    IState(ep.state).name, ep.title, ep.torrent.progress if ep.torrent else -1, ep.library.dateadded if ep.library else 'none'))

