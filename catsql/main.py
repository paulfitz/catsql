#!/usr/bin/env python

from __future__ import print_function

import argparse
from collections import OrderedDict
from io import StringIO, BytesIO
import json
import os
from sqlalchemy import *
from sqlalchemy.orm import create_session, mapper
from sqlalchemy.exc import ArgumentError, OperationalError, InvalidRequestError, SAWarning
from sqlalchemy.ext.declarative import declarative_base
import sys
import warnings

from catsql.nullify import Nullify

if sys.version_info[0] == 2:
    import unicodecsv as csv
else:
    import csv

warnings.simplefilter("ignore", category=SAWarning)

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
                        'data.sqlite3')

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

    parser.add_argument('--edit', required=False, action='store_true',
                        help='Edit original table in your favorite editor (multiple tables not yet supported)')

    parser.add_argument('--safe-null', required=False, action='store_true',
                        help='Encode nulls in a reversible way')

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
    except ImportError as e:
        print("Support library for this database not installed - {}".format(e))
        exit(1)
    except ArgumentError:
        import magic
        result = str(magic.from_file(url).lower())
        if 'sqlite' in result:
            url = 'sqlite:///' + url
            engine = create_engine(url)
            args.url = url
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

    work = None
    output_filename = None
    output_file = sys.stdout
    work_file = None

    try:
        if args.edit:
            import tempfile
            work = tempfile.mkdtemp()
            output_filename = os.path.join(work, 'reference.csv')
            work_file = open(output_filename, 'wt')
            output_file = work_file
            output_in_csv = True
            args.safe_null = True
            args.save_bookmark = [ os.path.join(work, 'bookmark.json') ]

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

            primary_key = table.primary_key
            if len(primary_key) >= 1:
                rows = rows.order_by(*primary_key)
            elif len(table.c) >= 1:
                rows = rows.order_by(*table.c)

            if len(tables_so_far) > 0:
                if output_in_csv:
                    print("ERROR:",
                          "More than one table in CSV output "
                          "(maybe do '--table {}'?)".format(tables_so_far[0]),
                          file=sys.stderr)
                    exit(1)
                print("", file=output_file)
            if table_name != '_chancer_table_':
                if not output_in_csv:
                    print(table_name, file=output_file)
                    print('=' * len(table_name), file=output_file)
            columns = table.columns.keys()
            header_writer = CsvRowWriter()

            header = header_writer.writerow(list(column for column in columns if ok_column(column)))
            print(header, file=output_file)
            if not output_in_csv:
                print('-' * len(header), file=output_file)
            if not args.count:
                # csv spec is that eol is \r\n; we ignore this for our purposes
                # for good reasons that unfortunately there isn't space to describe
                # here on the back of this envelope
                csv_writer = csv.writer(output_file, lineterminator='\n')
                if args.safe_null:
                    nullify = Nullify()
                    for row in rows:
                        csv_writer.writerow(list(nullify.encode_null(cell)
                                                 for c, cell in enumerate(row)
                                                 if ok_column(columns[c])))
                else:
                    for row in rows:
                        csv_writer.writerow(list(cell for c, cell in enumerate(row)
                                                 if ok_column(columns[c])))
                del csv_writer
            else:
                ct = rows.count()
                print("({} row{})".format(ct, '' if ct == 1 else 's'), file=output_file)
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

        if args.edit:
            work_file.close()
            work_file = None
            from shutil import copyfile
            edit_filename = os.path.join(work, 'variant.csv')
            copyfile(output_filename, edit_filename)
            from subprocess import call
            EDITOR = os.environ.get('EDITOR', 'nano')
            call([EDITOR, edit_filename])
            call(['patchsql', args.url] +
                 ['--table'] + tables_so_far + 
                 ['--follow', output_filename, edit_filename] + 
                 ['--safe-null'])

    finally:
        if work:
            if work_file:
                try:
                    work_file.close()
                except:
                    pass
                work_file = None
            import shutil
            shutil.rmtree(work)
            work = None

if __name__ == "__main__":
    main()
