from catsql.filter import Filter
import os
from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session


class Database(object):
    def __init__(self, url, verbose=False, tables=None, can_create=False):
        self.url = url
        self._full_url = self.url
        self.verbose = verbose
        self.tables = tables
        self.can_create = can_create
        self.connect_database()

    def connect_database(self):
        self.Base = declarative_base()
        try:
            self.engine = create_engine(self.url, echo=self.verbose)
        except ImportError as e:
            print("Support library for this database not installed - {}".format(e))
            exit(1)
        except ArgumentError:
            if os.path.exists(self.url) or self.can_create:
                try:
                    # maybe this is a local sqlite database?
                    sqlite_url = 'sqlite:///{}'.format(self.url)
                    self.engine = create_engine(sqlite_url, echo=self.verbose)
                    self._full_url = sqlite_url
                except ArgumentError:
                    # no joy, recreate the original problem and die.
                    self.engine = create_engine(self.url, echo=self.verbose)
            else:
                raise
        only = None
        if self.tables:
            only = list(self.tables)
        self.Base.metadata.reflect(self.engine, only=only)

        self._session = create_session(bind=self.engine)

    @property
    def session(self):
        return self._session

    @property
    def full_url(self):
        return self._full_url

    @property
    def tables_metadata(self):
        return self.Base.metadata.tables

    def query(self, columns=None):
        return Filter(self, columns=columns)
