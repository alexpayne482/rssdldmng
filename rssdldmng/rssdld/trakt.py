import re
import logging

log = logging.getLogger(__name__)
logging.getLogger("trakt.core").setLevel(logging.WARNING)


# login to trakt first
# python -c "import trakt; trakt.init(store=True)"

class Trakt():

    def __init__(self, username, slist=None, reportprogress=False):
        self.username = username
        self.list = slist
        self.reportprogress = reportprogress

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
            shows = []
        return shows

    def setCollected(self, showname, season, episode):
        if not self.reportprogress:
            return True
        import trakt.users
        try:
            ep = trakt.tv.TVEpisode(showname, season, episode)
            ep.add_to_collection()
        except (trakt.errors.NotFoundException, Exception) as e:
            print('WRN: cannot set collected {:s} S{:02d}E{:02d} [{:}]'.format(showname, season, episode, e))
            return False
        return True

    def setWatched(self, showname, season, episode):
        if not self.reportprogress:
            return True
        import trakt.users
        try:
            ep = trakt.tv.TVEpisode(showname, season, episode)
            ep.mark_as_seen()
        except (trakt.errors.NotFoundException, Exception) as e:
            print('WRN: cannot set watched {:s} S{:02d}E{:02d} [{:}]'.format(showname, season, episode, e))
            return False
        return True
