import sys, os, re, json, logging, urllib

_LOGGER = logging.getLogger(__name__)

import rssdldmng.config as config_util
from rssdldmng.restserver import RESTHttpServer

class RSSdldApiServer(RESTHttpServer):
    def __init__(self, port, mng):
        self.routes = {
#            r'^/$'          : {'file': 'web/index.html', 'media_type': 'text/html'},
            r'^/config$'   : {'GET': self.get_config, 'media_type': 'application/json'},
            r'^/shows$'    : {'GET': self.get_shows, 'media_type': 'application/json'},
            r'^/latest$'   : {'GET': self.get_latest, 'media_type': 'application/json'},
            r'^/status$'   : {'GET': self.get_status, 'media_type': 'application/json'},
            r'^/add/'      : {'POST': self.add_show, 'media_type': 'application/json'},
            r'^/remove/'   : {'POST': self.remove_show, 'media_type': 'application/json'},
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
        return self.manager.get_status()

    def add_show(self, handler):
        show = urllib.parse.unquote(handler.path[5:])
        _LOGGER.debug("add_show: {0}".format(show))
        from rssdldmng.__main__ import save_config
        try:
            sn = self.manager.config['feeds'][0]['filters']['seriesname']
        except:
            sn = []
        sn.append(show)
        self.manager.config['feeds'][0]['filters']['seriesname'] = sn
        save_config(self.manager.config)
        return "OK"

    def remove_show(self, handler):
        show = urllib.parse.unquote(handler.path[8:])
        _LOGGER.debug("remove_show: {0}".format(show))
        from rssdldmng.__main__ import save_config
        try: 
            sn = self.manager.config['feeds'][0]['filters']['seriesname']
            if show in sn:
                sn.remove(show)
                self.manager.config['feeds'][0]['filters']['seriesname'] = sn
                save_config(self.manager.config)
                return "OK"
        except:
            pass
        return "Not Found"


