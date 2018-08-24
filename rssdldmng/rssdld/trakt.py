import sys, os, time
import re, json
import logging

log = logging.getLogger(__name__)
logging.getLogger("trakt.core").setLevel(logging.WARNING)


## login to trakt first
## python -c "import trakt; trakt.init(store=True)"

class Trakt():

    def __init__(self, username, slist=None):
        self.username = username
        self.list = slist

    def getShows(self):
        shows = []
        import trakt.users
        try:
            if self.list and self.list.lower() != 'watchlist':
                slist = trakt.users.User(self.username).get_list(self.list)
            else:
                slist = trakt.users.User(self.username).watchlist_shows
            for s in slist:
                if type(s) is trakt.tv.TVShow:
                    shows.append(re.sub('[\\/:"*?<>|]+', '', s.title))
        except Exception as e:
            log.warn('cannot get trakt list {0} for user {1} [{2}]'.format(self.list, self.username, e))
        return shows

    def setCollected(self, showname, season, episode):
        import trakt.users
        try:
            ep = trakt.tv.TVEpisode(showname, season, episode)
            ep.add_to_collection()
        except Exception as e:
            log.warn('cannot set collected {0} S{1}E{2} [{3}]'.format(showname, season, episode, e))
            return False
        return True

    def setWatched(self, showname, season, episode):
        import trakt.users
        try:
            ep = trakt.tv.TVEpisode(showname, season, episode)
            ep.mark_as_seen()
        except Exception as e:
            log.warn('cannot set watched {0} S{1}E{2} [{3}]'.format(showname, season, episode, e))
            return False
        return True


