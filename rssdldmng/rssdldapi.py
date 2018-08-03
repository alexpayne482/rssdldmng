import sys, os, re, json, logging, urllib

_LOGGER = logging.getLogger(__name__)

import rssdldmng.config as config_util
from rssdldmng.restserver import RESTHttpServer
#https://codepen.io/anon/pen/EpEmev
class RSSdldApiServer(RESTHttpServer):
    def __init__(self, port, mng):
        self.routes = {
            r'^/$'             : {'file': '/index.html', 'media_type': 'text/html'},
            r'^\/(?!api\/).*$' : {'file': '/', 'media_type': 'text/html'},
            r'^/api/config$'   : {'GET': self.get_config, 'media_type': 'application/json'},
            r'^/api/shows$'    : {'GET': self.get_shows, 'media_type': 'application/json'},
            r'^/api/setshows$' : {'PUT': self.set_shows, 'media_type': 'application/json'},
            r'^/api/latest$'   : {'GET': self.get_latest, 'media_type': 'application/json'},
            r'^/api/status$'   : {'GET': self.get_status, 'media_type': 'application/json'},
        }
        self.manager = mng
        self.servedir = '.'#os.path.join(self.manager.config['cfgdir'], 'www')
        RESTHttpServer.__init__(self, '', port, self.routes, self.servedir)

    def get_config(self, handler):
        return self.manager.config

    def get_shows(self, handler):
        shows = []
        for feed in self.manager.config['feeds']:
            try:
                shows.extend(feed['filters']['seriesname'])
            except:
                pass
        return shows

    def set_shows(self, handler):
        shows = handler.get_payload()
        _LOGGER.debug("set_shows: {0}".format(shows))
        self.manager.config['feeds'][0]['filters']['seriesname'] = shows
        self.manager.save_config(self.manager.config)
        return 'OK'

    def get_latest(self, handler):
        return self.manager.get_latest()

    def get_status(self, handler):
        return self.manager.get_status()


