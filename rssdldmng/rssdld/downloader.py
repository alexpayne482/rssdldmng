import time
import re
import logging

import feedparser

from ..utils.sthread import ServiceThread

from .showsdb import ShowsDB
from .kodidb import KodiDB
from .episode import Episode, IState
from .transmission import Transmission
from .trakt import Trakt

log = logging.getLogger(__name__)


class Downloader(ServiceThread):
    """"
    A class to read rss feed and download it's items
    """

    def __init__(self, db_file, config):

        self.db_file = db_file
        self.config = config

        self.feeds = self.config['feeds']
        self.fconfig = self.config['filters']
        self.tconfig = self.config['transmission']
        self.kconfig = self.config.get('kodi', None)
        self.tkconfig = self.config.get('trakt', None)

        self.last_feed_poll = 0
        self.last_poll = 0

        self.db = None
        self.tc = None
        self.kd = None
        self.tk = None

        self.series = None

        ServiceThread.__init__(self)

    def serve_starting(self):
        # connect to DB
        self.db = ShowsDB(self.db_file)
        self.connectTrakt()
        log.info('Started downloader')

    def serve(self):
        # main loop
        ifeedpoll = self.config['feed_poll_interval']
        ipoll = self.config['poll_interval']

        if ifeedpoll > 0 and time.time() - self.last_feed_poll >= ifeedpoll:
            self.last_feed_poll = time.time()
            self.updateFilters()
            self.checkFeeds()

        if ipoll > 0 and time.time() - self.last_poll >= ipoll:
            self.last_poll = time.time()
            self.checkProgress()

    def serve_stop(self):
        log.debug('Stopping downloader')
        if self.tk and self.tk.auth_start:
            self.tk.cancel_authentication()

    def serve_stopped(self):
        log.info('Stopped downloader')

    def connectTrakt(self):
        if self.tkconfig is not None and self.tk is None:
            try:
                self.tk = Trakt(self.tkconfig)
                self.tk.authenticate()
            except Exception as e:
                log.error("FAILED to authenticate to Trakt [{}]".format(e))
                self.tk = None
                return False
        return True

    def connectTransmission(self):
        # connect to transmission
        if self.tconfig is not None and self.tc is None:
            try:
                log.debug('connect to transmission')
                self.tc = Transmission(self.tconfig)
            except Exception as e:
                log.error('FAILED to connect to transmission: exception [{0}]'.format(e))
                self.tc = None
                return False
        return True

    def connectKodi(self):
        # connect to kodi
        if self.kconfig is not None and self.kd is None:
            try:
                log.debug('connect to kodi')
                self.kd = KodiDB(self.kconfig)
            except Exception as e:
                log.error('FAILED to connect to kodi: exception [{0}]'.format(e))
                self.kd = None
                return False
        return True

    def updateFilters(self):
        series = []
        if 'series' in self.fconfig :
            if isinstance(self.fconfig['series'], list):
                log.debug('get series from config file')
                series.extend(self.fconfig['series'])
            elif isinstance(self.fconfig['series'], str):
                if self.fconfig['series'].startswith('trakt:'):
                    tklist = self.fconfig['series'].split(':')[1]
                    if self.tk:
                        log.debug('get series from Trakt')
                        # TODO: this should be done async ...
                        series.extend(self.tk.getTvShows(tklist))
                    else:
                        log.warn('not connected to Trakt: could not get series list')
                else:
                    log.debug('unsupported series filter string format')
            else:
                log.debug('unsupported series filter format')

        series = [re.sub('[\\/:"*?<>|]+', '', x).lower() for x in series]
        series = list(set(series))

        if len(series):
            log.debug('Series updated [{0}]: \n{1}'.format(len(series), str.join(', ', series)))
            self.series = series
        else:
            log.debug('No series filter will be applied')

    def checkFilter(self, ep):
        # filter out specials ???
        # if ep.season <= 0 or ep.episode <= 0:
        #    return False
        if self.series is not None:
            if ep.showname.lower() not in self.series:
                return False
        # if 'series' in self.fconfig and self.fconfig['series']:
        #     if ep.showname.lower() not in self.fconfig['series']:
        #         return False
        if 'quality' in self.fconfig and self.fconfig['quality']:
            if ep.quality not in self.fconfig['quality']:
                return False
        return True

    def getFeedEpisodes(self, feed):
        pfeed = feedparser.parse(feed)
        items = []
        for item in pfeed['items']:
            items.append(Episode(item))
        return items

    def checkFeeds(self):
        log.debug("-------------------------------------------------------------------------------")
        for feed in self.feeds:
            self.parseFeed(feed)

    def parseFeed(self, feed):
        log.info("check rss feed {0}".format(feed))

        total = 0
        added = 0
        skipped = 0

        for ep in self.getFeedEpisodes(feed):
            total += 1
            if not self.checkFilter(ep):
                log.debug('skipped f : %s', ep)
                skipped += 1
                continue
            dbep = self.db.getEpisode(ep.hash)
            if not dbep:
                ep.state = IState.NEW.value
                ep.set_dir(self.config['dir'])
                # TODO: ep.date = now()
                dbep = self.db.addEpisode(ep)
                log.debug('add to db : %s', dbep)
                added += 1
            else:
                log.debug('existing  : %s', dbep)

        strresult = "found {0} items: {1} accepted, {2} rejected".format(total, added, skipped)
        log.info(strresult)
        return strresult

    def checkProgress(self):
        log.debug("-------------------------------------------------------------------------------")
        log.info("checking progress ...")

        self.connectTransmission()
        self.connectKodi()

        if self.tc is None:
            self.dumpStats()
            return

        # add new items in transmission
        log.debug("adding new items to transmission")
        for ep in self.db.getEpisodes(IState.NEW.value):
            # if item already in kodi, skip it
            if self.kd and self.kd.getVideo(ep.showname, ep.season, ep.episode):
                log.debug('in library: %s', ep)
                self.db.updateEpisodeState(ep, IState.AVAILABLE.value)
                continue
            # download item if not already downloading
            tcitem = self.tc.get(ep.hash)
            if not tcitem:
                self.tc.add(ep.link, ep.dir)
                log.debug('add to tr : %s', ep)
            else:
                log.debug('existing  : %s', ep)
            self.db.updateEpisodeState(ep, IState.DOWNLOADING.value)

        # add finished items in kodi
        log.debug("check items finished downloading")
        for ep in self.db.getEpisodes(IState.DOWNLOADING.value):
            tcitem = self.tc.get(ep.hash)
            if tcitem:
                # log.debug('tc: %s', tcitem)
                if tcitem.progress != 100.0:
                    log.debug('downloadin: %s', ep)
                    self.tc.start(ep.hash)  # might be paused
                else:
                    log.debug('finished  : %s', ep)
                    self.tc.stop(ep.hash)
                    self.db.updateEpisodeState(ep, IState.FINISHED.value)
            else:
                self.tc.add(ep.link, ep.dir)
                log.debug('add to tr : %s', ep)

        log.debug("remove finished items from transmission")
        for ep in self.db.getEpisodes(IState.FINISHED.value):
            # remove from transmission
            tcitem = self.tc.get(ep.hash)
            if tcitem:
                log.debug('remove tr : %s', ep)
                self.tc.remove(ep.hash)
            if self.kd is not None:
                # add to kodi
                self.kd.updateLibPath(ep.dir)
                # update state to UPDATING
                self.db.updateEpisodeState(ep, IState.UPDATING.value)

        if self.kd is None:
            self.dumpStats()
            return

        # mark items found in kodi as available
        log.debug("add items to kodi")
        for ep in self.db.getEpisodes(IState.UPDATING.value):
            ke = self.kd.getVideo(ep.showname, ep.season, ep.episode)
            if ke and ke.file:
                log.debug('in library: %s', ep)
                # update state to AVAILABLE
                self.db.updateEpisodeState(ep, IState.AVAILABLE.value)
                # remove from transmission
                self.tc.remove(ep.hash)
                # set collected in trakt
                if self.tk:
                    self.tk.setCollected(ep.showname, ep.season, ep.episode)
            else:
                log.debug('not found : %s', ep)
                # trigger another lib update
                self.kd.updateLibPath(ep.dir)

        # ckeck if available items were watched
        log.debug("mark watched items")
        for ep in self.db.getEpisodes(IState.AVAILABLE.value):
            ke = self.kd.getVideo(ep.showname, ep.season, ep.episode)
            if ke and ke.playcount >= 1:
                log.debug('watched   : %s', ep)
                # update state to WATCHED
                self.db.updateEpisodeState(ep, IState.WATCHED.value)
                # update watched state in trakt
                if self.tk:
                    self.tk.setWatched(ep.showname, ep.season, ep.episode)

        self.dumpStats()

    def dumpStats(self):
        # print stats
        log.info("new {}, downloading {}, finished {}, updating {}, available {}, watched {}, invalid {}".format(
                len(self.db.getEpisodes(IState.NEW.value)),
                len(self.db.getEpisodes(IState.DOWNLOADING.value)),
                len(self.db.getEpisodes(IState.FINISHED.value)),
                len(self.db.getEpisodes(IState.UPDATING.value)),
                len(self.db.getEpisodes(IState.AVAILABLE.value)),
                len(self.db.getEpisodes(IState.WATCHED.value)),
                len(self.db.getEpisodes(IState.NONE.value))
            ))

    # extern API

    def getEpisodesFull(self, state=-1, published=-1):
        lst = []
        for ep in self.db.getEpisodes(state, published):
            tr = {}
            ke = {}
            if self.tc:
                tr = self.tc.get(ep.hash)
            if self.kd:
                ke = self.kd.getVideo(ep.showname, ep.season, ep.episode)
            ep.torrent = tr
            ep.library = ke
            lst.append(ep)
            # s = json.dumps(ep, default=lambda x: x.__dict__)
            # log.info(s)
        return lst

    def getEpisodes(self, state=-1, published=-1):
        return self.db.getEpisodes(state, published)

    # manual state update
    def updateEpisode(self, ephash, state):
        dbep = self.db.getEpisode(ephash)
        if dbep:
            self.db.updateEpisodeState(dbep, state)
            if state is IState.AVAILABLE.value and self.tc is not None:
                self.tc.remove(ephash)
            if state is IState.WATCHED.value and self.tk is not None:
                self.tk.setWatched(dbep.showname, dbep.season, dbep.episode)
            return True
        return False

    def dumpDB(self):
        log.debug("get all db items with status")
        for ep in self.db.getEpisodes():
            log.info(ep)
