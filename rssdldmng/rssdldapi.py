import sys, os, re, json, logging, urllib

_LOGGER = logging.getLogger(__name__)

from rssdldmng.utils.restserver import RESTHttpServer


class RSSdldApiServer(RESTHttpServer):
    def __init__(self, port, mng):
        self.routes = {
            r'^/$'                  : {'file': '/index.html', 'media_type': 'text/html'},
            r'^\/(?!api\/).*$'      : {'file': '/', 'media_type': 'text/html'},
            r'^/api/config$'        : {'GET': self.get_config, 'media_type': 'application/json'},
            r'^/api/shows$'         : {'GET': self.get_shows, 'media_type': 'application/json'},
            r'^/api/latest$'        : {'GET': self.get_latest, 'media_type': 'application/json'},
            r'^/api/status$'        : {'GET': self.get_status, 'media_type': 'application/json'},

            r'^/api/checkfeed.*$'   : {'PUT': self.put_checkfeed, 'media_type': 'application/json'},
            r'^/api/db/.*$'         : {'GET': self.get_db, 'PUT': self.put_db, 'media_type': 'application/json'},

            #r'^/api/setshows$'      : {'PUT': self.put_shows, 'media_type': 'application/json'},
            r'^/api/trakt/list.*$'  : {'GET': self.get_traktlist, 'media_type': 'application/json'},
            r'^/api/test.*$'        : {'GET': self.test, 'media_type': 'application/json'},
        }
        self.manager = mng
        self.servedir = '.' #os.path.join(self.manager.config['cfgdir'], 'www')
        RESTHttpServer.__init__(self, '', port, self.routes, self.servedir)

    def get_config(self, handler):
        return self.manager.config

    def get_shows(self, handler):
        if not self.manager.downloader:
            return 'internal error'
        return self.manager.downloader.getSeries(True)

    def put_shows(self, handler):
        if type(self.manager.config['downloader']['series']) is str:
            return 'FAIL'
        shows = handler.get_payload()
        _LOGGER.debug("set_shows: {0}".format(shows))
        self.manager.config['downloader']['series'] = shows
        self.manager.save_config(self.manager.config)
        return 'OK'

    def get_latest(self, handler):
        return self.manager.get_latest(21)

    def get_status(self, handler):
        return self.manager.get_status(21)

    def get_traktlist(self, handler):
        args, params = self.get_args(handler.path, 4)
        if len(args) < 1:
            return 'no trakt username provided'

        from rssdldmng.rssdld.trakt import Trakt
        return Trakt(args[0], args[1] if len(args) >= 2 else 'watchlist').getShows()

    def put_checkfeed(self, handler):
        if not self.manager.downloader:
            return 'internal error'

        args, params = self.get_args(handler.path, 2)
        if 'feed' not in params:
            return 'no feed provided'

        res = self.manager.downloader.checkFeed(params['feed'])
        return res


    def get_db(self, handler):
        if not self.manager.downloader:
            return 'internal error'

        args, params = self.get_args(handler.path, 3)
        if len(args) < 1:
            return 'no action provided'

        if args[0] == 'dump' or args[0] == 'dumpall':
            state = -1
            if len(args) >= 2:
                state = int(args[1])
            if args[0] == 'dump':
                return [e.cleaned() for e in self.manager.downloader.getEpisodes(state=state)]
            else:
                return self.manager.downloader.getEpisodes(state=state)

        return 'invalid action'

    def put_db(self, handler):
        if not self.manager.downloader:
            return 'internal error'

        args, params = self.get_args(handler.path, 3)
        if len(args) < 1:
            return 'no action provided'

        if args[0] == 'set':
            if len(args) < 3:
                return 'no hash provided or state'
            if not self.manager.update_episode(args[1], int(args[2])):
                return 'FAIL'
            return 'OK'

#            hash = params['hash'] if 'hash' in params else None
#            showname = params['show'] if 'show' in params else None
#            season = params['season'] if 'season' in params else -1
#            episode = params['episode'] if 'episode' in params else -1
#            return [e.cleaned() for e in self.manager.downloader.getEpisodes(state=state)]

        return 'invalid action'

    def test(self, handler):
        #self.manager.downloader.tk.setCollected(None, "elementary", 1, 1)
        return 'OK'

    def get_args(self, path, index):
        args = path.split('/')[index:]
        lastarg = args[-1].split('?')
        args[-1] = lastarg[0]
        paramlist = lastarg[1] if len(lastarg) > 1 else None
        params = {}
        if paramlist:
            for p in paramlist.split('&'):
                if '=' in p:
                    params[p.split('=')[0]] = p.split('=')[1]
                else:
                    params[p] = True

        return (args, params)

