import sys
import logging
import feedparser

from ..pysqlw import pysqlw
from .episode import Episode

log = logging.getLogger(__name__)

class ShowsDB(object):

    def __init__(self, db_path):
        self.table = 'episodes'
        self.db_path = db_path
        self.db = pysqlw(db_type='sqlite', db_path=db_path)
        #self.db.wrapper.cursor.execute('DROP TABLE `{table}`'.format(table=self.table))
        try:
            self.db.get(self.table)
        except:
            self.db.wrapper.cursor.execute(
                ''' CREATE TABLE `{table}` (
                        `title`     TEXT,
                        `published` NUMERIC,
                        `link`      TEXT,
                        `uid`       INTEGER,
                        `showid`    INTEGER,
                        `showname`  TEXT,
                        `hash`      TEXT,
                        `quality`   TEXT,
                        `episode`   INTEGER,
                        `season`    INTEGER,
                        `dir`       TEXT,
                        `state`     INTEGER,
                        PRIMARY KEY(`hash`));'''
            .format(table=self.table))
            self.db.wrapper.dbc.commit()

    def hasEpisode(self, ihash):
        if self.db.where('hash', ihash).get(self.table):
            return True
        return False

    def addEpisode(self, item):
        if not self.hasEpisode(item.hash):
            self.db.insert(self.table, item.__dict__)
            return item
        return None

    def updateEpisode(self, item):
        if self.hasEpisode(item.hash):
            self.db.where('hash', item.hash).update(self.table, item.__dict__)
        else:
            self.db.insert(self.table, item.__dict__)

    def updateEpisodeState(self, item, state):
        if self.hasEpisode(item.hash):
            item.state = state
            self.db.where('hash', item.hash).update(self.table, item.__dict__)

    def getEpisode(self, ihash):
#        log.debug('find hash %s', ihash)
        rows = self.db.where('hash', ihash).get(self.table)
#        log.debug(rows)
        if rows:
            return Episode(entries=rows[0])
        return None

        # create new db cursor so it could be acceseed from different thread
    def getEpisodes(self, state=-1, published=-1):
        dbreq = pysqlw(db_type='sqlite', db_path=self.db_path)
        if state >= 0:
            #rows = self.db.where('state', state).get(self.table)
            dbreq = dbreq.where('state', state)
        if published >= 0:
            dbreq = dbreq.where('published', published, '>')

        rows = dbreq.get(self.table)
        dbreq.close()
        items = []
        for row in rows:
            items.append(Episode(entries=row))
        return items

    def close(self):
        self.db.close()
