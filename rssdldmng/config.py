import json

from rssdldmng.const import (
    __version__,
    CONFIG_FILE,
    DB_FILE,
    API_PORT
)

class JsonConvert(object):
    mappings = {}
     
    @classmethod
    def class_mapper(clsself, d):
        for keys, cls in clsself.mappings.items():
            if keys.issuperset(d.keys()):   # are all required arguments present?
                return cls(**d)
        else:
            # Raise exception instead of silently returning None
            raise ValueError('Unable to find a matching class for object: {!s}'.format(d))
     
    @classmethod
    def complex_handler(clsself, Obj):
        if hasattr(Obj, '__dict__'):
            return Obj.__dict__
        else:
            raise TypeError('Object of type %s with value of %s is not JSON serializable' % (type(Obj), repr(Obj)))
 
    @classmethod
    def register(clsself, cls):
        clsself.mappings[frozenset(tuple([attr for attr,val in cls().__dict__.items()]))] = cls
        return cls
 
    @classmethod
    def ToJSON(clsself, obj):
        return json.dumps(obj.__dict__, default=clsself.complex_handler, indent=4)
 
    @classmethod
    def FromJSON(clsself, json_str):
        return json.loads(json_str, object_hook=clsself.class_mapper)
     
    @classmethod
    def ToFile(clsself, obj, path):
        with open(path, 'w') as jfile:
            jfile.writelines([clsself.ToJSON(obj)])
        return obj
 
    @classmethod
    def FromFile(clsself, filepath):
        result = None
        with open(filepath, 'r') as jfile:
            result = clsself.FromJSON(jfile.read())
        return result


class ConfigBase(object):
    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.__dict__)
        
    # def __setattr__(self, key, value):
    #     if key is 'final':
    #         super().__setattr__(key, value)
    #         for val in self.__dict__:
    #             if isinstance(self.__dict__[val], ConfigBase):
    #                 self.__dict__[val].__setattr__(key, value)
    #     if 'final' not in self.__dict__:
    #         super().__setattr__(key, value)

@JsonConvert.register
class FiltersConfig(ConfigBase):
    #__slots__ = ['series', 'quality']
    def __init__(self, series:[str]=None, quality:[str]=None):
        self.series = [] if series is None else series
        self.quality = [] if quality is None else quality

@JsonConvert.register
class TraktConfig(ConfigBase):
    #__slots__ = ['clientid', 'clientsecret', 'username', 'tmdbapikey', 'reportprogress']
    def __init__(self, clientid:str=None, clientsecret:str=None, username:str=None, tmdbapikey:str=None, reportprogress:bool=None):
        self.clientid = '' if clientid is None else clientid
        self.clientsecret = '' if clientsecret is None else clientsecret
        self.username = '' if username is None else username
        self.tmdbapikey = '' if tmdbapikey is None else tmdbapikey
        self.reportprogress = False if reportprogress is None else reportprogress

@JsonConvert.register
class RemoteServerConfig(ConfigBase):
    #__slots__ = ['host', 'port', 'username', 'password']
    def __init__(self, host:str=None, port:int=None, username:str=None, password:str=None):
        self.host = 'localhost' if host is None else host
        self.port = 8080 if port is None else port
        self.username = 'user' if username is None else username
        self.password = 'password' if password is None else password

@JsonConvert.register
class DownloaderConfig(ConfigBase):
    #__slots__ = ['dir', 'feeds', 'feed_poll_interval', 'poll_interval', 'filters', 'trakt', 'transmission', 'kodi']
    def __init__(self, dir:str=None, feeds:[str]=None, feed_poll_interval:int=None, poll_interval:int=None, 
                 filters:FiltersConfig=None, trakt:TraktConfig=None, transmission:RemoteServerConfig=None, kodi:RemoteServerConfig=None):
        self.dir = '/media/Series/{seriesname}/Season{seasonno:02}/' if dir is None else dir
        self.feeds = ['http://showrss.info/other/all.rss'] if feeds is None else feeds
        self.feed_poll_interval = 300 if feed_poll_interval is None else feed_poll_interval
        self.poll_interval = 60 if poll_interval is None else poll_interval
        self.filters = FiltersConfig() if filters is None else filters
        self.trakt = TraktConfig() if trakt is None else trakt
        self.transmission = RemoteServerConfig() if transmission is None else transmission
        self.kodi = RemoteServerConfig() if kodi is None else kodi

@JsonConvert.register
class LoggingConfig(ConfigBase):
    #__slots__ = ['file', 'level']
    def __init__(self, file:str=None, level:str=None):
        self.file = '' if file is None else file
        self.level = 'info' if level is None else level

@JsonConvert.register
class Config(ConfigBase):
    #__slots__ = ['apiport', 'downloader', 'logging']
    def __init__(self, apiport:int=None, downloader:DownloaderConfig=None, logging:LoggingConfig=None):
        self.apiport = API_PORT if apiport is None else apiport
        self.downloader = DownloaderConfig() if downloader is None else downloader
        self.logging = LoggingConfig() if logging is None else logging
        #self.final = True
