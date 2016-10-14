def add_options(parser):

    parser.add_argument('catsql_database_url',
                        help='Database url or filename.  Examples: '
                        'sqlite:///data.db, '
                        'mysql://user:pass@host/db, '
                        'postgres[ql]://user:pass@host/db, '
                        'data.sqlite3')

    parser.add_argument('--column', action='append',
                        help='Column to include (defaults to all columns). '
                        'Can be a comma separated list of multiple columns.')

    parser.add_argument('--count', default=False, action='store_true',
                        help='Show row counts instead of actual data.')

    parser.add_argument('--csv', default=False, action='store_true',
                        help='Output strictly in CSV format. Only one table can be shown.')

    parser.add_argument('--distinct', default=False, action='store_true',
                        help='Show distinct rows only, hiding duplicates.')

    parser.add_argument('--edit', required=False, action='store_true',
                        help='Edit original table in your favorite editor. '
                        'Respects $EDITOR environment variable.')

    parser.add_argument('--grep', nargs=1, required=False, default=None,
                        help='Search cells for occurrence of a text fragment. '
                        'Translated to SQL query, performed by database.')

    parser.add_argument('--json', nargs=1, required=False, default=None,
                        help='Save results to a json file. Only one table allowed.')

    parser.add_argument('--limit', nargs=1, required=False, default=None,
                        help='Maximum number of rows per table.')

    parser.add_argument('--load-bookmark', required=False, action='store_true',
                        help='Load a set of filters from a file.')

    parser.add_argument('--output', nargs=1, required=False, default=None,
                        help='Save output to specified file.  Incompatible with --edit.')

    parser.add_argument('--safe-null', required=False, action='store_true',
                        help='Encode nulls in a reversible way.')

    parser.add_argument('--save-bookmark', nargs=1, required=False, default=None,
                        help='Save the current set of filters specified to a file.')

    parser.add_argument('--sql', action='append',
                        help='Add a raw SQL filter for rows to include.  Example: '
                        '"total < 1000", "created_at > now() - interval \'1 day\'". '
                        'Tables that don\'t have the columns mentioned are '
                        'omitted.'
    )

    parser.add_argument('--table', action='append',
                        help='Table to include (defaults to all tables). '
                        'Can be a comma separated list of multiple tables.')

    parser.add_argument('--terse', default=False, action='store_true',
                        help='Hide any columns with predetermined values.')

    parser.add_argument('--types', default=False, action='store_true',
                        help='Show column types instead of actual data.')

    parser.add_argument('--value', action='append',
                        help='R|Add a column=value filter. Example:\n'
                        '  --value id=ID --value name=Jupiter\n'
                        'As a shortcut you can also do:\n'
                        '  --id ID --name Jupiter')

    parser.add_argument('--verbose', default=False, action='store_true',
                        help='Show raw SQL queries as they are made.')

    parser.add_argument('--order', action='append',
                        help='Columns to order by. '
                        'Can be a comma separated list of columns names. '
                        'Add + or - to end of name to specify ascending or descending '
                        'order.  Specify "none" to disable ordering completely '
                        '(by default we always try to apply some order)')

