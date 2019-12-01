import time
import re
import logging
import json
import urllib.parse
from enum import Enum

import feedparser

from ..utils.sthread import ServiceThread

from .showsdb import ShowsDB
from .kodidb import KodiDB
from .episode import Episode, IState
from .transmission import Transmission
from .trakt import Trakt

log = logging.getLogger(__name__)

class SkipReason(Enum):
    NONE = 1
    SERIES = 2
    QUALITY = 3
    SEASON = 4

class Downloader(ServiceThread):
    """"
    A class to read rss feed and download it's items
    """

    def __init__(self, db_file, config):

        self.db_file = db_file
        self.config = config

        self.last_feed_poll = 0
        self.last_poll = 0

        self.db = ShowsDB(self.db_file)
        self.tc = None
        self.kd = None
        self.tk = None

        self.epFilter = {}

        ServiceThread.__init__(self)

    def serve_starting(self):
        # connect to DB
        self.connectTrakt()
        log.info('Started downloader')

    def serve(self):
        # main loop
        if self.config.feed_poll_interval > 0 and time.time() - self.last_feed_poll >= self.config.feed_poll_interval:
            self.last_feed_poll = time.time()
            self.updateFilter()
            self.checkFeeds()

        if self.config.poll_interval > 0 and time.time() - self.last_poll >= self.config.poll_interval:
            self.last_poll = time.time()
            self.checkProgress()

    def serve_stop(self):
        log.debug('Stopping downloader')
        if self.tk and self.tk.auth_start:
            self.tk.cancel_authentication()

    def serve_stopped(self):
        log.info('Stopped downloader')

    def connectTrakt(self):
        if self.config.trakt is not None and self.tk is None:
            try:
                log.debug('connect to Trakt as {}'.format(self.config.trakt.username))
                self.tk = Trakt(self.config.trakt)
                self.tk.authenticate()
            except Exception as e:
                log.error("FAILED to authenticate/connect to Trakt [{}]".format(e))
                self.tk = None
                return False
        return True

    def connectTransmission(self):
        # connect to transmission
        if self.config.transmission is not None and self.tc is None:
            try:
                log.debug('connect to Transmission {}:{} as {}'.format(self.config.transmission.host, self.config.transmission.port, self.config.transmission.username))
                self.tc = Transmission(self.config.transmission)
            except Exception as e:
                log.error('FAILED to connect to Transmission: exception [{0}]'.format(e))
                self.tc = None
                return False
        return True

    def connectKodi(self):
        # connect to kodi
        if self.config.kodi is not None and self.kd is None:
            try:
                log.debug('connect to Kodi {}:{} as {}'.format(self.config.kodi.host, self.config.kodi.port, self.config.kodi.username))
                self.kd = KodiDB(self.config.kodi)
            except Exception as e:
                log.error('FAILED to connect to Kodi: exception [{0}]'.format(e))
                self.kd = None
                return False
        return True

    def updateFilter(self):
        self.epFilter = {}

        series = []
        for item in self.config.filters.series:
            if item.startswith('trakt:'):
                tklist = item.split(':')[1]
                if self.tk and tklist:
                    log.debug('get series from Trakt')
                    # TODO: this should be done async ...
                    series.extend(self.tk.getTvShows(tklist))
                else:
                    log.warn('Not connected to Trakt: could not get series list {}'.format(tklist))
            else:
                series.insert(item)
        series = [re.sub('[\\/:"*?<>|]+', '', x).lower() for x in series]
        series = list(set(series))

        quality = self.config.filters.quality

        self.epFilter['series'] = series if len(series) else None
        self.epFilter['quality'] = quality if len(quality) else None

        log.debug('filter updated: {}'.format(self.epFilter))

    def checkFilter(self, ep, filter):
        # filter out specials ???
        # if ep.season <= 0 or ep.episode <= 0:
        #    return False
        if filter.get('series') is not None:
            if ep.showname.lower() not in filter.get('series'):
                #log.debug('{} not in series'.format(ep.showname.lower()))
                return SkipReason.SERIES
        if filter.get('quality') is not None:
            if ep.quality not in filter.get('quality'):
                #log.debug('{} not in quality'.format(ep.quality))
                return SkipReason.QUALITY
        if filter.get('season') is not None:
            if ep.season not in filter.get('season'):
                #log.debug('{} not in season {}'.format(ep.season, filter.get('season')))
                return SkipReason.SEASON
        return SkipReason.NONE

    def getFeedEpisodes(self, feed):
        pfeed = feedparser.parse(feed)
        items = []
        for item in pfeed['items']:
            items.append(Episode(item))
        return items

    def checkFeeds(self):
        log.debug("-------------------------------------------------------------------------------")
        for feed in self.config.feeds:
            self.parseFeed(feed, self.epFilter)

    def parseFeed(self, feed, fltr):
        filter = self.epFilter.copy()
        if fltr is not None:
            filter.update(fltr)

        total = 0
        added = 0
        skipped = 0
        existing = 0

        log.info("check rss feed {0}, filter {1}".format(feed, filter))

        for ep in self.getFeedEpisodes(feed):
            total += 1
            res = self.checkFilter(ep, filter)
            if res != SkipReason.NONE:
                log.debug('%-10s: %s', 'SK_' + SkipReason(res).name, ep)
                skipped += 1
            else:
                dbep = self.db.getEpisode(ep.hash)
                if not dbep:
                    ep.state = IState.NEW.value
                    ep.set_dir(self.config.dir)
                    # TODO: ep.date = now()
                    dbep = self.db.addEpisode(ep)
                    log.debug('add to db : %s', dbep)
                    added += 1
                else:
                    log.debug('existing  : %s', dbep)
                    existing += 1

        log.info("found {0} items: {1} accepted, {2} rejected".format(total, added, skipped))
        htmlresult = "Found {0} items:<br><ul><li>{1} existing</li><li>{2} new</li><li>{3} skipped</li></ul>".format(total, existing, added, skipped)
        return htmlresult

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
            poster = None
            if self.tc:
                tr = self.tc.get(ep.hash)
            # if self.kd:
            #     ke = self.kd.getVideo(ep.showname, ep.season, ep.episode)
            #     if ke:
            #         poster = ke.art.get('season.poster', None)
            #         if not poster:
            #             poster = ke.art.get('tvshow.poster', None)
            #         if poster:
            #             if poster.startswith("image://"):
            #                 poster = poster[8:]
            #             if poster.endswith("/"):
            #                 poster = poster[:-1]
            #             poster = urllib.parse.unquote(poster)
            # else:
            if self.tk:
                poster = self.tk.getPoster(ep.showname)
            ep.poster = poster
            ep.torrent = tr
            ep.library = ke
            lst.append(ep)
            log.debug("{} poster".format(ep, poster))
            #log.debug(json.dumps(ep, default=lambda x: x.__dict__))
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
