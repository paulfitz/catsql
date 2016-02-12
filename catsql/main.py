#!/usr/bin/env python

from __future__ import print_function
import argparse
import csv
from io import StringIO, BytesIO
from sqlalchemy import *
from sqlalchemy.orm import create_session, mapper
from sqlalchemy.exc import ArgumentError, OperationalError, InvalidRequestError
from sqlalchemy.ext.declarative import declarative_base
import sys

# Temporary workaround for python2/python3 utf8 issues
class CsvRowWriter:
    def __init__(self):
        self.queue = StringIO()
        self.queue2 = BytesIO()
        self.writer = None

    def writerow(self, row):
        try:
            self.writer = csv.writer(self.queue, lineterminator='')
            row = [str(s) for s in row]
            self.writer.writerow(row)
            return self.queue.getvalue()
        except TypeError:
            self.writer = csv.writer(self.queue2, lineterminator='')
            row = [str(s) for s in row]
            self.writer.writerow(row)
            return self.queue2.getvalue()

def main():

    parser = argparse.ArgumentParser(description='Quickly display (part of) a database.')

    parser.add_argument('url', help='Database url or filename.  Examples: '
                        'sqlite:///data.db, '
                        'mysql://user:pass@host/db, '
                        'postgres[ql]://user:pass@host/db, '
                        'data.sqlite3, '
                        'data.csv')

    parser.add_argument('--table', nargs='*', required=False, default=None,
                        help='Tables to include (defaults to all tables)')

    parser.add_argument('--row', nargs='*', required=False, default=None,
                        help='Filters for rows to include.  Examples: '
                        '"total < 1000", "name = \'american_bison\'". '
                        'Tables that don\'t have the columns mentioned are '
                        'omitted.'
    )

    parser.add_argument('--context', nargs='*', required=False, default=None,
                        help='key=value filters')

    parser.add_argument('--hide-context', default=False, action='store_true',
                        help='Hide any columns mentioned in context filters')

    parser.add_argument('--bare', default=False, action='store_true',
                        help='Show table and column names, skip actual data.')

    parser.add_argument('--csv', default=False, action='store_true',
                        help='Output strictly in CSV format.')

    args = parser.parse_args()

    url = args.url
    tables = args.table
    if tables is not None:
        tables = set(tables)
    row_filter = args.row
    bare = args.bare
    output_in_csv = args.csv

    Base = declarative_base()
    try:
        engine = create_engine(url)
    except ArgumentError:
        import magic
        result = str(magic.from_file(url).lower())
        if 'sqlite' in result:
            url = 'sqlite:///' + url
            engine = create_engine(url)
        elif 'text' in result:
            engine = create_engine('sqlite://')
            with open(url) as f:
                table = None
                metadata = MetaData(bind=engine)
                cf = csv.DictReader(f, delimiter=',')
                for row in cf:
                    if table is None:
                        table = Table('_chancer_table_', metadata, 
                                      Column('_chancer_id_', Integer, primary_key=True),
                                      *(Column(rowname, String()) for rowname in row.keys()))
                        table.create()
                    table.insert().values(**row).execute()

                class CsvTable(object): pass
                mapper(CsvTable, table)
        else:
            engine = create_engine(url)

    Base.metadata.reflect(engine)

    session = create_session(bind=engine)

    tables_so_far = []

    context_columns = set()
    def ok_column(name):
        if name == '_chancer_id_':
            return False
        if args.hide_context:
            if name in context_columns:
                return False
        return True

    for table_name, table in Base.metadata.tables.items():
        if tables is not None:
            if table_name not in tables:
                continue
        rows = session.query(table)
        if row_filter is not None:
            for filter in row_filter:
                rows = rows.filter(text(filter))
            try:
                count = rows.count()
            except OperationalError as e:
                # should cache these and show if no results at all found
                continue

        if args.context is not None:
            applicable = True
            for context in args.context:
                if '=' in context:
                    key, value = context.split('=', 1)
                    f = {}
                    f[key] = value
                    try:
                        rows = rows.filter_by(**f)
                    except InvalidRequestError as e:
                        applicable = False
                    context_columns.add(key)
                else:
                    context_columns.add(context)
            if not applicable:
                continue

        if len(tables_so_far) > 0:
            if output_in_csv:
                print("ERROR:",
                      "More than one table in CSV output "
                      "(maybe do '--table {}'?)".format(tables_so_far[0]),
                      file=sys.stderr)
                exit(1)
            print("")
        if table_name != '_chancer_table_':
            if not output_in_csv:
                print(table_name)
                print('=' * len(table_name))
        columns = table.columns.keys()
        header_writer = CsvRowWriter()

        header = header_writer.writerow(list(column for column in columns if ok_column(column)))
        print(header)
        if not output_in_csv:
            print('-' * len(header))
        if not bare:
            csv_writer = csv.writer(sys.stdout)
            for row in rows:
                csv_writer.writerow(list(cell for c, cell in enumerate(row) if ok_column(columns[c])))
            del csv_writer
        else:
            print("...")
        tables_so_far.append(table_name)

if __name__ == "__main__":
    main()
