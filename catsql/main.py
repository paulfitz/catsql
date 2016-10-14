#!/usr/bin/env python

from __future__ import print_function

import argparse
import errno
from collections import OrderedDict
from io import StringIO, BytesIO
import json
import os
from sqlalchemy import *
from sqlalchemy import types
from sqlalchemy.exc import (ArgumentError, CompileError, OperationalError, InvalidRequestError,
                            SAWarning)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session, load_only, mapper
from sqlalchemy.sql import expression, functions
import sys
import warnings

from catsql import cmdline
from catsql.nullify import Nullify

if sys.version_info[0] == 2:
    import unicodecsv as csv
else:
    import csv

warnings.simplefilter("ignore", category=SAWarning)

# Get approximate length of header
class CsvRowWriter(object):
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

class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)

class Viewer(object):
    def __init__(self, args, remainder, sys_args):
        self.args = args
        self.sys_args = sys_args
        self.failure = False
        self.values = None
        self.setup_filters(args)
        self.connect_database()
        self.process_remainder(remainder)

    def decomma(self, lst):
        if not lst:
            return lst
        lst = [l.split(',') for l in lst]
        return [item for sublist in lst for item in sublist]

    def setup_filters(self, args):
        self.url = args.catsql_database_url
        self.tables = self.decomma(args.table)
        self.selected_columns = self.decomma(args.column)
        self.ordering = self.decomma(args.order)

        self.context_columns = set()
        self.context_filters = dict()
        if args.load_bookmark:
            with open(self.url, 'r') as fin:
                nargs = json.loads(fin.read())
            self.url = nargs['url']
            self.tables = set(nargs['table'])
            self.args.distinct = nargs.get('distinct', False)
            self.selected_columns = nargs.get('column', [])
            self.context_filters = nargs['context']
            self.context_columns = set(nargs['hidden_columns'])
            if args.value is None:
                self.args.value = []

        if self.tables is not None:
            self.tables = set(self.tables)
        self.row_filter = args.sql
        self.output_in_csv = args.csv
        self.output_in_json = args.json

        if args.value is not None:
            for context in args.value:
                if '=' in context:
                    key, value = context.split('=', 1)
                    self.context_filters[key] = value
                    self.context_columns.add(key)
                else:
                    self.context_columns.add(context)

    def connect_database(self):
        self.Base = declarative_base()
        try:
            self.engine = create_engine(self.url, echo=self.args.verbose)
        except ImportError as e:
            print("Support library for this database not installed - {}".format(e))
            exit(1)
        except ArgumentError:
            try:
                # maybe this is a local sqlite database?
                sqlite_url = 'sqlite:///{}'.format(self.url)
                self.engine = create_engine(sqlite_url, echo=self.args.verbose)
                self.url = self.args.catsql_database_url = sqlite_url
            except ArgumentError:
                # no joy, recreate the original problem and die.
                self.engine = create_engine(self.url, echo=self.args.verbose)

        only = None
        if self.tables:
            only = list(self.tables)
        self.Base.metadata.reflect(self.engine, only=only)

        self.session = create_session(bind=self.engine)

    def process_remainder(self, remainder):
        column_names = set()
        if len(remainder) == 0:
            return
        for table in self.Base.metadata.tables.values():
            column_names |= set(table.columns.keys())
        if 'catsql_database_url' in column_names:
            column_names.remove('catsql_database_url')
        parser = argparse.ArgumentParser()
        cmdline.add_options(parser)
        for name in sorted(column_names):
            try:
                parser.add_argument('--{}'.format(name), nargs=1, default=None)
            except argparse.ArgumentError:
                column_names.remove(name)
        self.values = vars(parser.parse_args(self.sys_args))
        dud = []
        for key, val in self.values.items():
            if (key not in column_names) or val is None:
                dud.append(key)
        for key in dud:
            del self.values[key]
        for key, val in self.values.items():
            self.values[key] = val[0]

    def ok_column(self, name):
        if self.args.terse:
            if name in context_columns:
                return False
        if self.selected_columns:
            if name not in self.selected_columns:
                return False
        return True

    def start_table(self, table_name, columns):
        self.header_shown = False
        self.header_considered = False
        self.table_name = table_name
        self.columns = columns
        if self.selected_columns:
            self.columns = self.selected_columns

    def show_header_on_need(self):
        if self.header_shown or self.header_considered:
            return True
        self.header_considered = True
        if len(self.tables_so_far) > 0:
            if self.output_in_csv or self.output_in_json:
                self.failure = True
                self.tables_so_far.append(self.table_name)
                return False
            print("", file=self.output_file)
        if not (self.output_in_csv or self.output_in_json):
            print('== {} =='.format(self.table_name), file=self.output_file)
        if not self.output_in_json:
            header_writer = CsvRowWriter()

            header = header_writer.writerow(list(column for column in self.columns 
                                                 if self.ok_column(column)))
            print(header, file=self.output_file)
            if not self.output_in_csv:
                print('-' * len(header), file=self.output_file)
        self.header_shown = True
        self.tables_so_far.append(self.table_name)
        return True

    def add_grep(self, table, query, sequence, case_sensitive):
        # functions.concat would be neater, but doesn't seem to translate
        # correctly on sqlite
        parts = ''
        for idx, column in enumerate(table.columns):
            if not self.ok_column(column.name):
                continue
            if parts != '':
                parts = parts + ' // '
            part = functions.coalesce(expression.cast(column,
                                                      types.Unicode),
                                      '')
            parts = parts + part
        if case_sensitive:
            query = query.filter(parts.contains(sequence))
        else:
            query = query.filter(parts.ilike('%%' + sequence + '%%'))
        return query

    def show(self):

        self.tables_so_far = []

        work = None
        output_filename = None
        self.output_file = sys.stdout
        work_file = None
        self.start_table(None, None)

        try:
            if self.args.edit:
                import tempfile
                work = tempfile.mkdtemp()
                output_filename = os.path.join(work, 'reference.csv')
                work_file = open(output_filename, 'wt')
                self.output_file = work_file
                self.output_in_csv = True
                self.args.safe_null = True
                self.args.save_bookmark = [ os.path.join(work, 'bookmark.json') ]
            elif self.args.output:
                self.output_file = open(self.args.output[0], 'wt')

            table_items = self.Base.metadata.tables.items()

            viable_tables = []
            for table_name, table in sorted(table_items):

                if self.tables is not None:
                    if table_name not in self.tables:
                        continue

                if self.selected_columns is not None:
                    ok = True
                    for name in self.selected_columns:
                        if name not in table.c:
                            ok = False
                    if not ok:
                        continue
                    rows = self.session.query(*[table.c[name] for name in self.selected_columns])
                else:
                    rows = self.session.query(table)

                if self.args.distinct:
                    rows = rows.distinct()

                if self.row_filter is not None:
                    for filter in self.row_filter:
                        rows = rows.filter(text(filter))
                    try:
                        count = rows.count()
                    except OperationalError as e:
                        # should cache these and show if no results at all found
                        continue

                if self.args.value is not None:
                    try:
                        rows = rows.filter_by(**self.context_filters)
                    except InvalidRequestError as e:
                        continue

                if self.values is not None:
                    try:
                        for key, val in self.values.items():
                            rows = rows.filter(table.c[key] == val)
                    except InvalidRequestError as e:
                        continue

                if self.args.grep:
                    rows = self.add_grep(table, rows, self.args.grep[0], case_sensitive=False)

                if self.args.order:
                    if 'none' in self.args.order:
                        pass
                    else:
                        orders = []
                        for name in self.ordering:
                            c = name[-1]
                            order = name
                            if c == '+' or c == '-':
                                order = order[:-1]
                            order = table.c[order]
                            if c == '+':
                                order = asc(order)
                            elif c == '-':
                                order = desc(order)
                            orders.append(order)
                        rows = rows.order_by(*orders)

                else:
                    primary_key = table.primary_key
                    if self.selected_columns:
                        rows = rows.order_by(*[table.c[name] for name in self.selected_columns])
                    elif len(primary_key) >= 1:
                        rows = rows.order_by(*primary_key)
                    elif len(table.c) >= 1:
                        rows = rows.order_by(*table.c)

                if self.args.limit:
                    rows = rows.limit(int(self.args.limit[0]))

                self.header_shown = False
                self.start_table(table_name, table.columns.keys())
                viable_tables.append(table_name)

                if self.args.types:
                    types = []
                    for name in self.columns:
                        if not self.ok_column(name):
                            continue
                        try:
                            column = table.c[name]
                            sql_type = column.type
                            sql_name = str(column.type)  # make sure not nulltype
                        except CompileError:
                            sql_name = None
                        types.append(sql_name)
                    rows = [types]

                if self.output_in_json:
                    if not self.show_header_on_need():
                        continue
                    self.save_as_json(table, rows, self.output_in_json[0])
                elif not self.args.count:
                    # csv spec is that eol is \r\n; we ignore this for our purposes
                    # for good reasons that unfortunately there isn't space to describe
                    # here on the back of this envelope
                    csv_writer = csv.writer(self.output_file, lineterminator='\n')
                    if self.args.safe_null:
                        nullify = Nullify()
                        for row in rows:
                            if not self.show_header_on_need():
                                continue
                            csv_writer.writerow(list(nullify.encode_null(cell)
                                                     for c, cell in enumerate(row)
                                                     if self.ok_column(self.columns[c])))
                    else:
                        for row in rows:
                            if not self.show_header_on_need():
                                continue
                            csv_writer.writerow(list(cell for c, cell in enumerate(row)
                                                     if self.ok_column(self.columns[c])))
                    del csv_writer
                else:
                    self.show_header_on_need()
                    ct = rows.count()
                    print("({} row{})".format(ct, '' if ct == 1 else 's'), file=self.output_file)

            if len(self.tables_so_far) == 0 and len(viable_tables) == 1:
                self.show_header_on_need()

            if self.args.save_bookmark:
                with open(self.args.save_bookmark[0], 'w') as fout:
                    link = OrderedDict()
                    link['url'] = self.args.catsql_database_url
                    link['table'] = list(self.tables) if self.tables else None
                    link['column'] = self.selected_columns
                    link['distinct'] = self.args.distinct
                    link['context'] = self.context_filters
                    link['hidden_columns'] = sorted(self.context_columns)
                    link['sql'] = self.args.sql
                    fout.write(json.dumps(link, indent=2))

            if self.args.edit and not self.failure:
                work_file.close()
                work_file = None
                from shutil import copyfile
                edit_filename = os.path.join(work, 'variant.csv')
                copyfile(output_filename, edit_filename)
                from subprocess import call
                editor = os.environ.get('TABLE_EDITOR', None)
                if not editor:
                    editor = os.environ.get('EDITOR', 'nano')
                call([editor, edit_filename])
                call(['patchsql', self.url] +
                     ['--table'] + self.tables_so_far + 
                     ['--follow', output_filename, edit_filename] + 
                     ['--safe-null'])

        finally:
            if self.failure:
                print("ERROR: "
                      "More than one table in csv/json output, consider adding:",
                      file=sys.stderr)
                for name in self.tables_so_far:
                    print("  --table {}".format(name),
                          file=sys.stderr)

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


    def save_as_json(self, table, rows, filename):
        result = OrderedDict()
        result['count'] = 0
        result['meta'] = {
            'generator': 'catsql'
        }
        results = result['results'] = []
        names = []
        idxs = []
        for idx, column in enumerate(self.columns):
            if not self.ok_column(column):
                continue
            idxs.append(idx)
            names.append(column)
        for row in rows:
            od = OrderedDict()
            for i, idx in enumerate(idxs):
                od[names[i]] = row[idx]
            results.append(od)
        result['count'] = len(results)
        with open(filename, 'w') as fout:
            fout.write(json.dumps(result, indent=2))

def catsql(sys_args):

    parser = argparse.ArgumentParser(description='Quickly display and edit a slice of a database.',
                                     formatter_class=SmartFormatter)

    cmdline.add_options(parser)
    args, remainder = parser.parse_known_args(sys_args)
    viewer = Viewer(args, remainder, sys_args)
    viewer.show()


def main():
    try:
        catsql(sys.argv[1:])
    except IOError as error:
        if error.errno == errno.EPIPE:
            # totally benign e.g. pipe through head/tail
            pass
        else:
            raise

if __name__ == "__main__":
    main()
