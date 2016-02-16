#!/usr/bin/env python

from __future__ import print_function
import argparse
import daff
import json
from sqlalchemy.exc import SAWarning
import sys
import warnings

from catsql.daffsql.sqlalchemy_database import SqlAlchemyDatabase
from catsql.nullify import Nullify

if sys.version_info[0] == 2:
    import unicodecsv as csv
else:
    import csv

warnings.simplefilter("ignore", category=SAWarning)

def fix_nulls(table, active):
    if not active:
        return
    nullify = Nullify()
    for row in table:
        for i in range(0, len(row)):
            row[i] = nullify.decode_null(row[i])

def main():

    parser = argparse.ArgumentParser(description='Patch a database.')

    parser.add_argument('url', help='Sqlalchemy-compatible database url')

    parser.add_argument('--patch', nargs=1, required=False, default=None,
                        help='csv patch file from daff')

    parser.add_argument('--follow', nargs=2, required=False, default=None,
                        help='two csv files to compare, patch from their diff')

    parser.add_argument('--table', nargs=1, required=True, default=None,
                        help='Table to patch')

    parser.add_argument('--safe-null', required=False, action='store_true',
                        help='Decode nulls in a reversible way')

    args = parser.parse_args()

    url = args.url
    tables = args.table

    db = SqlAlchemyDatabase(url)
    st = daff.SqlTable(db, daff.SqlTableName(tables[0]))

    patch = None

    if args.patch:
        with open(args.patch[0], 'rt') as fin:
            reader = csv.reader(fin)
            patch = list(csv.reader(fin))
            patch = daff.Coopy.tablify(patch)

    if args.follow:
        with open(args.follow[0], 'rt') as fin:
            reader = csv.reader(fin)
            table0 = list(csv.reader(fin))
            fix_nulls(table0, args.safe_null)
        with open(args.follow[1], 'rt') as fin:
            reader = csv.reader(fin)
            table1 = list(csv.reader(fin))
            fix_nulls(table1, args.safe_null)
        patch = daff.Coopy.diff(table0, table1)
        ansi_patch = daff.Coopy.diffAsAnsi(table0, table1)
        print(ansi_patch, file=sys.stderr, end='')

    daff_patch = daff.HighlightPatch(st, patch)
    daff_patch.apply()
    if db.events['skips'] != 0:
        print(" * {}".format(json.dumps(db.events),
                             file=sys.stderr))

if __name__ == "__main__":
    main()
