# -*- coding: utf-8 -*-
import logging
log = logging.getLogger(__name__)

from sqltype import sqltype

class sqlitew(sqltype):
    @property
    def required(self):
        return ['db_path']

    def connect(self):
        try:
            log.info('connecting to %s', self.args.get('db_path'))
            import sqlite3
            self.dbc = sqlite3.connect(self.args.get('db_path'))
            self.dbc.row_factory = self._sqlite_dict_factory
            #self.dbc.set_trace_callback(print)
            self.cursor = self.dbc.cursor()
        except Exception as e:
            log.error('connect to %s failed', self.args.get('db_path'))
            log.info(e)
            return False
        return True

    def format(self, item):
        return '?'

    def _sqlite_dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
