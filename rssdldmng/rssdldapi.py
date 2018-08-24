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
            #r'^/api/setshows$'      : {'PUT': self.set_shows, 'media_type': 'application/json'},
            r'^/api/latest$'        : {'GET': self.get_latest, 'media_type': 'application/json'},
            r'^/api/status$'        : {'GET': self.get_status, 'media_type': 'application/json'},
            r'^/api/trakt/list.*$'  : {'GET': self.get_traktlist, 'media_type': 'application/json'},
            r'^/api/test.*$'        : {'GET': self.test, 'media_type': 'application/json'},
            r'^/api/setepisode$'    : {'PUT': self.set_episode, 'media_type': 'application/json'},
        }
        self.manager = mng
        self.servedir = '.'#os.path.join(self.manager.config['cfgdir'], 'www')
        RESTHttpServer.__init__(self, '', port, self.routes, self.servedir)

    def get_config(self, handler):
        return self.manager.config

    def get_shows(self, handler):
        if not self.manager.downloader:
            return 'internal error'
        return self.manager.downloader.getSeries(True)

    def set_shows(self, handler):
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
        if not self.manager.downloader:
            return 'internal error'
        args = handler.path.split('/')[4:]
        _LOGGER.debug("args: {0}".format(args))
        if len(args) < 1:
            return 'no trakt username provided'
        username = args[0]
        wlist = args[1] if len(args) >= 2 else 'watchlist' 
        return self.manager.downloader.getTraktShows(username, wlist)

    def set_episode(self, handler):
        data = handler.get_payload()
        if 'hash' not in data or 'state' not in data:
            return 'FAIL [invalid input]'
        _LOGGER.debug("set_episode {0} state to {1}".format(data['hash'], data['state']))
        if not self.manager.update_episode(data['hash'], data['state']):
            return 'FAIL'
        return 'OK'

    def test(self, handler):
        self.manager.downloader.setCollected(None, "elementary", 1, 1)
        return 'OK'

