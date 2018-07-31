import sys, os, re, json, logging

_LOGGER = logging.getLogger(__name__)

from rssdldmng.restserver import RESTHttpServer

class RSSdldApiServer(RESTHttpServer):
    def __init__(self, port, mng):
        self.routes = {
#            r'^/$'          : {'file': 'web/index.html', 'media_type': 'text/html'},
            r'^/config$'   : {'GET': self.get_config, 'media_type': 'application/json'},
            r'^/shows$'    : {'GET': self.get_shows, 'media_type': 'application/json'},
            r'^/latest$'   : {'GET': self.get_latest, 'media_type': 'application/json'},
            r'^/status$'   : {'GET': self.get_status, 'media_type': 'application/json'},
            r'^/add/'      : {'PUT': self.add_show, 'media_type': 'application/json'},
            r'^/remove/'   : {'PUT': self.remove_show, 'media_type': 'application/json'},
        }
        self.manager = mng
        RESTHttpServer.__init__(self, '', port, self.routes)

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

    def get_latest(self, handler):
        return self.manager.get_latest()

    def get_status(self, handler):
        return None

    def add_show(self, handler):
        return None

    def remove_show(self, handler):
        return None


