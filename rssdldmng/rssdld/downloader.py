import sys, os, time
import re, json
import logging
from enum import Enum

import feedparser

from ..utils.sthread import ServiceThread

from .showsdb import ShowsDB
from .kodidb import KodiDB
from .episode import Episode, IState
from .transmission import Transmission
from .trakt import Trakt

log = logging.getLogger(__name__)


class RSSdld(ServiceThread):
    """"
    A class to read rss feed and download it's items
    """

    def __init__(self, db_file, config):

        self.db_file = db_file
        self.config = config

        self.feeds = self.config['feeds']
        self.dconfig = self.config['downloader']
        self.tconfig = self.config['transmission']
        self.kconfig = self.config['kodi']

        self.last_feed_poll = 0
        self.last_lib_update = 0

        self.db = None
        self.tc = None
        self.kd = None

        self.trakt = self.config['trakt'] if 'trakt' in self.config else {}
        self.tk = None

        self.series = None

        ServiceThread.__init__(self)


    def serve_starting(self):
        # connect to DB
        self.db = ShowsDB(self.db_file)
        if 'username' in self.trakt:
            self.tk = Trakt(self.trakt['username'], 
                            self.trakt['list'] if 'list' in self.trakt else None,
                            self.trakt['report'] if 'report' in self.trakt else False)
        self.updateSeries()
        log.info('Started downloader')
        #log.debug('Series  filter {0}'.format(self.getSeries()))

    def serve(self):
        # main loop
        if self.dconfig['feed_poll_interval'] > 0 and time.time() - self.last_feed_poll >= self.dconfig['feed_poll_interval']:
            self.last_feed_poll = time.time()
            self.updateSeries()
            self.checkFeeds()

        if self.dconfig['lib_update_interval'] > 0 and time.time() - self.last_lib_update >= self.dconfig['lib_update_interval']:
            self.last_lib_update = time.time()
            self.checkProgress()

    def serve_stopped(self):
        log.info('Stopped downloader')


    def updateSeries(self):
        if 'series' not in self.dconfig and not self.tk:
            return None

        series = []
        if self.tk:
            series.extend(self.tk.getShows())
        if 'series' in self.dconfig:
            series.extend(self.dconfig['series'])
        series = [re.sub('[\\/:"*?<>|]+', '', x).lower() for x in series]
        series = list(set(series))

        log.debug('Series updated [{0}]: \n{1}'.format(len(series), str.join(', ', series)))
        self.series = series

        return series


    def connectTransmission(self):
        # connect to transmission
        if self.tc == None:
            try:
                log.debug('connect to transmission')
                self.tc = Transmission(self.tconfig)
            except Exception as e:
                log.warn('FAILED to connect to transmission')
                log.debug('exception [{0}]'.format(e))
                self.tc = None
                return False
        return True


    def connectKodi(self):
        # connect to kodi
        if self.kd == None:
            try:
                log.debug('connect to kodi')
                self.kd = KodiDB(self.kconfig)
            except Exception as e:
                log.warn('FAILED to connect to kodi')
                log.debug('exception [{0}]'.format(e))
                self.kd = None
                return False
        return True


    def getFeedEpisodes(self, feed):
        pfeed = feedparser.parse(feed)
        items = []
        for item in pfeed['items']:
            items.append(Episode(item))
        return items


    def checkFilter(self, ep):
        # filter out specials ???
        #if ep.season <= 0 or ep.episode <= 0:
        #    return False
        if self.series is not None:
            if ep.showname.lower() not in self.series:
                return False
        if 'quality' in self.dconfig and self.dconfig['quality']:
            if ep.quality not in self.dconfig['quality']:
                return False
        return True


    def checkFeeds(self):
        # check rss feeds for new items
        for feed in self.feeds:
            log.info("check rss feed {0}".format(feed))
            total = 0; added = 0; skipped = 0;
            for ep in self.getFeedEpisodes(feed):
                total += 1
                if not self.checkFilter(ep):
                    log.debug('skipped f : %s', ep)
                    skipped += 1
                    continue
                dbep = self.db.getEpisode(ep.hash)
                if not dbep:
                    ep.state = IState.NEW.value
                    ep.set_dir(self.config['downloader']['dir'])
                    # TODO: ep.date = now()
                    dbep = self.db.addEpisode(ep)
                    log.debug('add to db : %s', dbep)
                    added += 1
                else:
                    log.debug('existing  : %s', dbep)
            log.info("found {0} items: {1} accepted, {2} rejected".format(total, added, skipped))

    def checkProgress(self):
        log.info("checking progress")
        self.connectTransmission()
        self.connectKodi()

        if self.tc == None:
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
                #log.debug('tc: %s', tcitem)
                if tcitem.progress != 100.0:
                    log.debug('downloadin: %s', ep)
                    self.tc.start(ep.hash) # might be paused
                else:
                    log.debug('finished  : %s', ep)
                    self.tc.stop(ep.hash)
                    if self.kd != None:
                        # add to kodi
                        self.kd.updateLibPath(ep.dir)
                        # update state to UPDATING
                        self.db.updateEpisodeState(ep, IState.UPDATING.value)
            else:
                self.tc.add(ep.link, ep.dir)
                log.debug('add to tr : %s', ep)

        if self.kd == None: return

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


    def getEpisodesFull(self, state=-1, published=-1):
        lst = []
        for ep in self.db.getEpisodes(state, published):
            tr = {}
            ke = {}
            if self.tc: 
                tr = self.tc.get(ep.hash)
            if self.kd:
                ke = self.kd.getVideo(ep.showname, ep.season, ep.episode)
            ep.torrent = tr;
            ep.library = ke;
            lst.append(ep)
            #s = json.dumps(ep, default=lambda x: x.__dict__)
            #log.info(s)
        return lst


    def getEpisodes(self, state=-1, published=-1):
        return self.db.getEpisodes(state, published)


    def updateEpisode(self, ephash, state):
        dbep = self.db.getEpisode(ephash)
        if dbep:
            self.db.updateEpisodeState(dbep, state)
            if state == IState.AVAILABLE.value and self.tc != None:
                self.tc.remove(ephash)
            if state == IState.WATCHED.value and self.tk != None:
                self.tk.setWatched(dbep.showname, dbep.season, dbep.episode)
            return True
        return False


    def dumpStats(self):
        # print stats
        log.debug("new {0}, downloading {1}, updating {2}, available {3}, watched {4}, invalid {5}".format(
                len(self.db.getEpisodes(IState.NEW.value)),
                len(self.db.getEpisodes(IState.DOWNLOADING.value)),
                len(self.db.getEpisodes(IState.UPDATING.value)),
                len(self.db.getEpisodes(IState.AVAILABLE.value)),
                len(self.db.getEpisodes(IState.WATCHED.value)),
                len(self.db.getEpisodes(IState.NONE.value))
            ))


    def dumpDB(self):
        log.debug("get all db items with status")
        for ep in self.db.getEpisodes():
            log.info(ep)
