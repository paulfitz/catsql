from catsql.filter import Filter
import os
from shutil import copyfile
from sqlalchemy import Column, create_engine, Integer, MetaData, String, Table
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session, mapper
import sys

if sys.version_info[0] == 2:
    import unicodecsv as csv
else:
    import csv


class Database(object):
    def __init__(self, url, verbose=False, tables=None, schema=None, can_create=False):
        self.url = url
        self._full_url = self.url
        self.verbose = verbose
        self.tables = tables
        self.schema = schema
        self.can_create = can_create
        self.csv = None
        self.table = None
        self.connect_database()

    def finalize(self, changed):
        if not changed:
            # no changes
            return
        if not self.csv:
            # changes already applied externally
            return
        self.save_csv(self.csv)

    def connect_database(self):
        meta = MetaData()
        if self.schema:
            meta.schema = self.schema
        self.Base = declarative_base(metadata=meta)
        if '://' not in self.url and self.url.lower().endswith('.csv'):
            # special case for csv file - just load into memory
            self.engine = self.wrap_csv(self.url)
        else:
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

    def wrap_csv(self, url):
        engine = create_engine('sqlite://')
        self.csv = url
        with open(url) as f:
            metadata = MetaData(bind=engine)
            cf = csv.DictReader(f, delimiter=',')
            names = dict([(name, name or ('col%d' % i)) for i, name in enumerate(cf.fieldnames)])
            # if '_id_' not in cf.fieldnames:
            #    cols = cols + [Column('_id_', Integer, primary_key=True)]
            cols = [Column(names[rowname], String(), primary_key=(rowname == 'id'))
                    for rowname in cf.fieldnames]
            table = Table('_table_', metadata, *cols)
            table.create()
            for row in cf:
                row = dict((names[name], val) for name, val in row.items())
                table.insert().values(**row).execute()

            class CsvTable(object):
                pass
            mapper(CsvTable, table, primary_key=[Column('ROWID', Integer)])
            self.table = table
        return engine

    def save_csv(self, fname):
        if os.path.exists(fname):
            copyfile(fname, '{}.bak'.format(fname))
        with open(fname, 'wb') as fout:
            writer = csv.writer(fout)
            writer.writerow([c.name for c in self.table.columns][1:])
            for row in self.table.select().order_by('ROWID').execute():
                writer.writerow(row[1:])

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
