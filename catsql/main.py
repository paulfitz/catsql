#!/usr/bin/env python

from __future__ import print_function
import sys
import os

if sys.version_info < (3, 0):
    # upgrade to python3 if available, for utf8 safety
    try:
        os.execvp("python3", ["python3", __file__] + sys.argv[1:])
    except OSError:
        pass

import argparse
from collections import OrderedDict
import csv
from io import StringIO, BytesIO
import json
from sqlalchemy import *
from sqlalchemy.orm import create_session, mapper
from sqlalchemy.exc import ArgumentError, OperationalError, InvalidRequestError
from sqlalchemy.ext.declarative import declarative_base
import sys

# Get approximate length of header
class CsvRowWriter:
    def __init__(self):
        self.writer = None

    def writerow(self, row):
        row = [str(s) for s in row]
        try:
            queue = StringIO()
            self.writer = csv.writer(queue, lineterminator='')
            self.writer.writerow(row)
        except TypeError:
            queue = BytesIO()
            self.writer = csv.writer(queue, lineterminator='')
            self.writer.writerow(row)
        return queue.getvalue()

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

    parser.add_argument('--count', default=False, action='store_true',
                        help='Show row counts instead of actual data.')

    parser.add_argument('--csv', default=False, action='store_true',
                        help='Output strictly in CSV format.')

    parser.add_argument('--save-bookmark', nargs=1, required=False, default=None,
                        help='File to save link information in')

    parser.add_argument('--load-bookmark', required=False, action='store_true',
                        help='File to load link information from')


    args = parser.parse_args()

    url = args.url
    tables = args.table

    context_columns = set()
    context_filters = dict()
    if args.load_bookmark:
        with open(url, 'r') as fin:
            nargs = json.loads(fin.read())
        url = nargs['url']
        tables = nargs['table']
        context_filters = nargs['context']
        context_columns = set(nargs['hidden_columns'])
        if args.context is None:
            args.context = []

    if tables is not None:
        tables = set(tables)
    row_filter = args.row
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

    def ok_column(name):
        if name == '_chancer_id_':
            return False
        if args.hide_context:
            if name in context_columns:
                return False
        return True
    if args.context is not None:
        for context in args.context:
            if '=' in context:
                key, value = context.split('=', 1)
                context_filters[key] = value
                context_columns.add(key)
            else:
                context_columns.add(context)

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
            try:
                rows = rows.filter_by(**context_filters)
            except InvalidRequestError as e:
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
        if not args.count:
            csv_writer = csv.writer(sys.stdout)
            for row in rows:
                csv_writer.writerow(list(cell for c, cell in enumerate(row) if ok_column(columns[c])))
            del csv_writer
        else:
            ct = rows.count()
            print("({} row{})".format(ct, '' if ct == 1 else 's'))
        tables_so_far.append(table_name)

    if args.save_bookmark:
        with open(args.save_bookmark[0], 'w') as fout:
            link = OrderedDict()
            link['url'] = args.url
            link['table'] = args.table
            link['context'] = context_filters
            link['hidden_columns'] = sorted(context_columns)
            link['row'] = args.row
            fout.write(json.dumps(link, indent=2))

if __name__ == "__main__":
    main()
