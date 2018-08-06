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

        ServiceThread.__init__(self)


    def serve_starting(self):
        # connect to DB
        self.db = ShowsDB(self.db_file)
        # update series filter from Trakt if required
        self.checkFilters()

        log.info('Started downloader')


    def serve(self):
        # main loop
        if self.dconfig['feed_poll_interval'] > 0 and time.time() - self.last_feed_poll >= self.dconfig['feed_poll_interval']:
            self.last_feed_poll = time.time()
            self.checkFeeds()

        if self.dconfig['feed_poll_interval'] > 0 and time.time() - self.last_lib_update >= self.dconfig['feed_poll_interval']:
            self.last_lib_update = time.time()
            self.checkProgress()


    def serve_stopped(self):
        log.info('Stopped downloader')


    def connectTransmission(self):
        # connect to transmission
        if self.tc == None:
            try:
                log.debug('connect to transmission')
                self.tc = Transmission(self.tconfig)
            except Exception as e:
                log.warn('connect to transmission failed [{0}]'.format(e))
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
                log.warn('connect to kodi failed [{0}]'.format(e))
                self.kd = None
                return False
        return True

## login to trakt first
## python -c "import trakt; trakt.init(store=True)"
## currently pytrackt is not working with PIN auth, waiting for fix
## should return trakt watchlist
    def getTraktShows(slef, username):
        shows = []
        try:
            import trakt.users
            u = trakt.users.User(username)
            if u:
                for s in u.watchlist_shows:
                    if type(s) is trakt.tv.TVShow:
                        shows.append(re.sub('[\\/:"*?<>|]+', '', s.title))
        except Exception as e:
            log.warn('connect to trakt failed [{0}]'.format(e))
        return shows

    def getFeedEpisodes(self, feed):
        pfeed = feedparser.parse(feed)
        items = []
        for item in pfeed['items']:
            items.append(Episode(item))
        return items

    def checkFilter(self, ep):
        if 'series' in self.dconfig and self.dconfig['series']:
            if ep.showname not in self.dconfig['series']:
                return False
        if 'quality' in self.dconfig and self.dconfig['quality']:
            if ep.quality not in self.dconfig['quality']:
                return False
        return True

    def checkFeeds(self):
        # check rss feeds for new items
        log.debug("check rss and add new items to db")
        for feed in self.feeds:
            for ep in self.getFeedEpisodes(feed):
                if not self.checkFilter(ep):
                    log.debug('skipped f : %s', ep)
                    continue
                dbep = self.db.getEpisode(ep.hash)
                if not dbep:
                    ep.state = IState.NEW.value
                    ep.set_dir(self.config['downloader']['dir'])
                    # TODO: ep.date = now()
                    dbep = self.db.addEpisode(ep)
                    log.debug('add to db : %s', dbep)
                else:
                    log.debug('existing  : %s', dbep)


    def checkProgress(self):
        self.connectTransmission()
        self.connectKodi()

        if self.tc == None:
            return

        # add new items in transmission
        log.debug("check new items and add them to transmission")
        for ep in self.db.getEpisodes(IState.NEW.value):
            # if item already in kodi, skip it
            if self.kd and self.kd.getVideo(ep.showname, ep.season, ep.episode):
                log.debug('in library : %s', ep)
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
        log.debug("check downloaded items and add them to kodi")
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
        log.debug("check items were added to kodi")
        for ep in self.db.getEpisodes(IState.UPDATING.value):
            ke = self.kd.getVideo(ep.showname, ep.season, ep.episode)
            if ke and ke.file:
                log.debug('in library: %s', ep)
                # update state to AVAILABLE
                self.db.updateEpisodeState(ep, IState.AVAILABLE.value)
                # remove from transmission
                self.tc.remove(ep.hash)
            else:
                log.debug('not found : %s', ep)
                #trigger another lib update
                self.kd.updateLibPath(ep.dir)


    def checkFilters(self):
        if 'series' in self.dconfig and type(self.dconfig['series']) is str:
            if self.dconfig['series'].startswith('trakt:'):
                traktcfg = self.dconfig['series'].split(':')[1:]
                self.dconfig['series'] = self.getTraktShows(traktcfg[0])

        log.debug('Series  filter {0}'.format(self.dconfig['series']))
        log.debug('Quality filter {0}'.format(self.dconfig['quality']))


    def dumpDB(self):
        log.debug("get all db items with status")
        for ep in self.db.getEpisodes():
            log.info(ep)


    def getDBitems(self, state=-1, published=-1):
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
