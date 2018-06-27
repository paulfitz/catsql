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


def patchsql(sys_args, database=None):

    parser = argparse.ArgumentParser(description='Patch a database.')

    parser.add_argument('url', help='Sqlalchemy-compatible database url')

    parser.add_argument('--patch', nargs=1, required=False, default=None,
                        help="A csv file describing the patch. In the "
                        "format output by daff.")

    parser.add_argument('--follow', nargs=2, required=False, default=None,
                        help="An alternative to --patch option.  Specify"
                        "two csv files to compare, and patch from their diff.")

    parser.add_argument('--table', nargs=1, required=True, default=None,
                        help='Table to which patch should be applied.')

    parser.add_argument('--schema', required=False, default=None,
                        help="Database schema to use (default: public).")

    parser.add_argument('--safe-null', required=False, action='store_true',
                        help='Decode nulls in a reversible way.')

    parser.add_argument('--quiet', required=False, action='store_true',
                       help='Do not show computed diff.')

    args = parser.parse_args(sys_args)

    url = args.url
    table = args.schema + '.' + args.table[0] if args.schema else args.table[0]

    if database:
        db = SqlAlchemyDatabase(database)
    else:
        db = SqlAlchemyDatabase(url)

    st = daff.SqlTable(db, daff.SqlTableName(table))

    patch = None

    if args.patch:
        with open(args.patch[0], 'rt') as fin:
            patch = list(csv.reader(fin))
            patch = daff.Coopy.tablify(patch)

    if args.follow:
        with open(args.follow[0], 'rt') as fin:
            table0 = list(csv.reader(fin))
            fix_nulls(table0, args.safe_null)
        with open(args.follow[1], 'rt') as fin:
            table1 = list(csv.reader(fin))
            fix_nulls(table1, args.safe_null)
        patch = daff.Coopy.diff(table0, table1)
        ansi_patch = daff.Coopy.diffAsAnsi(table0, table1)
        if not args.quiet:
            print(ansi_patch, file=sys.stderr, end='')

    if not patch:
        raise KeyError('please specify either --patch or --follow')

    daff_patch = daff.HighlightPatch(st, patch)
    daff_patch.apply()
    if db.events['skips'] != 0:
        print(" * {}".format(json.dumps(db.events),
                             file=sys.stderr))
    db.finalize()


def main():
    patchsql(sys.argv[1:])


if __name__ == "__main__":
    main()
