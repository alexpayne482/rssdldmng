import logging
import re
from kodipydent import Kodi


log = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)
log.setLevel(logging.WARNING)


class Video(object):

    def __init__(self, map):
        self.showtitle = map['showtitle']
        self.title = map['title']
        self.tvshowid = map['tvshowid']
        self.season = map['season']
        self.episode = map['episode']
        self.file = map['file']
        self.dateadded = map['dateadded']
        self.art = map['art']
        self.fanart = map['fanart']
        self.thumbnail = map['thumbnail']
        self.runtime = map['runtime']
        self.playcount = map['playcount']
        self.lastplayed = map['lastplayed']
        self.resume = map['resume']

    def __str__(self):
        if self.file is not None:
            return "{:<16s} {:<16s} S{:02d}E{:02d} {:s}".format(
                self.showtitle, self.title, self.season, self.episode, self.dateadded)
        else:
            return "None type"


class KodiDB(object):
    def __init__(self, config):
        log.debug("init: %s:%d u:%s", config['host'], config['port'], config['username'])
        self.kd = Kodi(hostname=config['host'], port=config['port'],
                       username=config['username'], password=config['password'])

    def getVideo(self, show, season, episode):
        try:
            log.debug('get video %s S%02dE%02d', show, season, episode)
            srsp = self.kd.VideoLibrary.GetTVShows()
            for s in srsp['result']['tvshows']:
                showname = re.sub('[\\/:"*?<>|]+', '', s["label"])
                if showname.lower().startswith(show.lower()):
                    log.debug('get video rsp: found show %s', s)
                    ersp = self.kd.VideoLibrary.GetEpisodes(
                            tvshowid=s['tvshowid'], season=season,
                            properties=['showtitle', 'tvshowid', 'season', 'episode', 'title', 'dateadded', 'playcount',
                                        'runtime', 'lastplayed', 'resume', 'art', 'fanart', 'thumbnail', 'file'])
                    for e in ersp['result']['episodes']:
                        # log.debug(e['episode'])
                        if e['episode'] == episode:
                            log.debug('get video rsp: found episode %s', e['file'])
                            return Video(e)
        except Exception:
            pass
        return None

    def updateLibPath(self, path):
        try:
            log.debug('update library path %s', path)
            rsp = self.kd.VideoLibrary.Scan(directory=path)
            log.debug('update library rsp: %s', rsp['result'])
            if rsp['result'] == 'OK':
                return True
        except KeyError:
            pass
        return False
