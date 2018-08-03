import sys
import logging
import feedparser

from ..pysqlw import pysqlw
from .episode import Episode

log = logging.getLogger(__name__)

class DBO():
    def __init__(self, db_path):
        self.db = pysqlw(db_type='sqlite', db_path=db_path)
    def __enter__(self):
        return self.db
    def __exit__(self, type, value, traceback):
        self.db.close()

class ShowsDB(object):

    def __init__(self, db_path):
        self.table = 'episodes'
        self.db_path = db_path
        self.createDB()

    def createDB(self):
        with DBO(self.db_path) as db:
            #db.wrapper.cursor.execute('DROP TABLE `{table}`'.format(table=self.table))
            try:
                db.get(self.table)
            except:
                db.wrapper.cursor.execute(
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
                db.wrapper.dbc.commit()

    def hasEpisode(self, db, ihash):
        if db.where('hash', ihash).get(self.table):
            return True
        return False

    def addEpisode(self, item):
        with DBO(self.db_path) as db:
            if not self.hasEpisode(item.hash, db):
                db.insert(self.table, item.__dict__)
                return item
        return None

    def updateEpisode(self, item):
        with DBO(self.db_path) as db:
            if self.hasEpisode(item.hash, db):
                db.where('hash', item.hash).update(self.table, item.__dict__)
            else:
                db.insert(self.table, item.__dict__)

    def updateEpisodeState(self, item, state):
        with DBO(self.db_path) as db:
            if self.hasEpisode(item.hash, db):
                item.state = state
                db.where('hash', item.hash).update(self.table, item.__dict__)

    def getEpisode(self, ihash):
        with DBO(self.db_path) as db:
            #log.debug('find hash %s', ihash)
            rows = db.where('hash', ihash).get(self.table)
            #log.debug(rows)
            if rows:
                return Episode(entries=rows[0])
        return None

        # create new db cursor so it could be acceseed from different thread
    def getEpisodes(self, state=-1, published=-1):
        items = []
        with DBO(self.db_path) as db:
            dbreq = db
            if state >= 0:
                #rows = self.db.where('state', state).get(self.table)
                dbreq = dbreq.where('state', state)
            if published >= 0:
                dbreq = dbreq.where('published', published, '>')

            rows = dbreq.get(self.table)
            for row in rows:
                items.append(Episode(entries=row))
        return items

