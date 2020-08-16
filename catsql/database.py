from catsql.filter import Filter
import decimal
import os
import re
from shutil import copyfile
from sqlalchemy import Column, create_engine, Float, Integer, MetaData, String, Table
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
        table_name = url
        table_name = re.sub(r'.*[/\\]', '', table_name)
        table_name = re.sub(r'[.].*$', '', table_name)
        table_name = table_name.lower()
        table_name = re.sub(r'[^a-z]', '', table_name)
        table_name = table_name or '_table_'
        data = self.read_csv(url)

        metadata = MetaData(bind=engine)
        cols = [
            Column(name,
                   data.column_types[idx],
                   primary_key=(name == 'id'))
            for idx, name in enumerate(data.column_names)
        ]
        has_primary_key = any((name == 'id') for name in data.column_names)
        if not has_primary_key:
            cols = [Column('id', Integer(), primary_key=True)] + cols
        table = Table(table_name, metadata, *cols)
        table.create()
        for idx, row in enumerate(data.rows):
            if not has_primary_key:
                row['id'] = idx + 1
            table.insert().values(**row).execute()

        class CsvTable(object):
            pass
        mapper(CsvTable, table)
        self.table = table
        return engine

    def read_csv(self, fname):
        class Data(object):
            pass
        data = Data()
        with open(fname) as f:
            cf = csv.DictReader(f, delimiter=',')
            data.rows = list(cf)
            data.column_names = cf.fieldnames
        data.column_types = [self.tweak_type(data, idx) for idx, _ in enumerate(data.column_names)]
        return data

    def tweak_type(self, data, idx):
        name = data.column_names[idx]
        strings = 0
        ints = 0
        floats = 0
        for row in data.rows:
            v = row[name]
            try:
                f = float(v)
                if abs(round(f) - f) > 0.001:
                    floats += 1
                else:
                    ints += 1
            except:
                strings += 1
            if strings > 50:
                break
        if strings > max([floats, ints]):
            return String()
        for row in data.rows:
            v = row[name]
            try:
                f = float(v)
                if ints > floats and abs(round(f) - f) < 0.001:
                    row[name] = int(f)
                else:
                    row[name] = f
            except:
                pass
        return Integer() if ints > floats else Float()

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
