import os
import sys
import logging
import math
import time
import re
from datetime import datetime, timedelta

from rssdldmng.rssdld.downloader import RSSdld
from rssdldmng.rssdld.episode import IState

_LOGGER = logging.getLogger(__name__)


from rssdldmng.rssdldapi import RSSdldApiServer


class RSSdldMng:

    def __init__(self, config):
        """Initialize new RSS Download Manager object."""
        self.config = config # type: dict
        self.downloader = None # type: RSSdld


    def run(self):
        try:
            _LOGGER.debug("Starting RSSDld core loop")
            #RSSdldApi.run(debug=True)
            self.http_server = RSSdldApiServer(8088, self)
            self.http_server.start()
            self.run_sync()
        except KeyboardInterrupt:
            _LOGGER.debug("Stopping RSSDld core loop")
            self.http_server.stop()
            self.stop_sync()


    def run_sync(self):
        self.downloader = RSSdld(self.config['dbpath'], self.config['feeds'], self.config['transmission'], self.config['kodi'])

        feed_poll_interval = self.config['feed_poll_interval']
        lib_update_interval = self.config['lib_update_interval']
        last_check_feeds = 0
        last_check_progress = 0

        while True:
            if feed_poll_interval > 0 and time.time() - last_check_feeds >= feed_poll_interval:
                last_check_feeds = time.time()
                self.check_feeds()

            if lib_update_interval > 0 and time.time() - last_check_progress >= lib_update_interval:
                last_check_progress = time.time()
                self.check_progress()

            time.sleep(10)

    def stop_sync(self):
        if self.downloader:
            self.downloader.close()
            self.downloader = None


    def check_feeds(self):
        if self.downloader:
            _LOGGER.debug("== checking feeds ...")
            self.downloader.checkFeeds()
            _LOGGER.debug("== checking feeds ... done")


    def check_progress(self):
        if self.downloader:
            _LOGGER.debug("== checking progress ...")
            self.downloader.checkProgress()
            _LOGGER.debug("== checking progress ... done")


    def dump_db_items(self):
        if self.downloader:
            self.downloader.dumpDB()
            for ep in self.downloader.getDBitems(published = (int(datetime.now().timestamp()) - 86400 * 7)):
                _LOGGER.info("{:<24s} S{:02d}E{:02d} {:12s} {:s} {:4d}% {:s}".format(ep.showname, ep.season, ep.episode, 
                    IState(ep.state).name, ep.title, ep.torrent.progress if ep.torrent else -1, ep.library.dateadded if ep.library else 'none'))

    def get_latest(self):
        if self.downloader:
            return self.downloader.getDBitems(published = (int(datetime.now().timestamp()) - 86400 * 7))
        return []

    def get_status(self):
        new = 0
        downloading = 0
        available = 0
        if self.downloader:
            for ep in self.downloader.getDBitems(published = (int(datetime.now().timestamp()) - 86400 * 7)):
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


