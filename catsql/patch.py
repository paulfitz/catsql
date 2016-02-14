#!/usr/bin/env python

from __future__ import print_function
import argparse
import daff
import json
import sys
import unicodecsv as csv

from catsql.daffsql.sqlalchemy_database import SqlAlchemyDatabase

def main():

    parser = argparse.ArgumentParser(description='Patch a database.')

    parser.add_argument('url', help='Sqlalchemy-compatible database url')

    parser.add_argument('--patch', nargs=1, required=False, default=None,
                        help='csv patch file from daff')

    parser.add_argument('--follow', nargs=2, required=False, default=None,
                        help='two csv files to compare, patch from their diff')

    parser.add_argument('--table', nargs=1, required=True, default=None,
                        help='Table to patch')

    args = parser.parse_args()

    url = args.url
    tables = args.table

    db = SqlAlchemyDatabase(url)
    st = daff.SqlTable(db, daff.SqlTableName(tables[0]))

    patch = None

    if args.patch:
        with open(args.patch[0], 'rb') as fin:
            reader = csv.reader(fin)
            patch = list(csv.reader(fin))
            patch = daff.Coopy.tablify(patch)

    if args.follow:
        with open(args.follow[0], 'rb') as fin:
            reader = csv.reader(fin)
            table0 = list(csv.reader(fin))
        with open(args.follow[1], 'rb') as fin:
            reader = csv.reader(fin)
            table1 = list(csv.reader(fin))
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
