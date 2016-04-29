catsql
======
[![Downloads](https://img.shields.io/pypi/dm/catsql.svg)](https://pypi.python.org/pypi/catsql)

Quickly display or edit part of a database.  Thin wrapper around SQLAlchemy.
Pronounced "cat-skill" for some reason.

Installation
------------

`pip install catsql`

Demo
----

![Terminal demo](https://cloud.githubusercontent.com/assets/118367/13240849/048e2834-d9b4-11e5-9510-7812f2fc1b71.gif)

Examples
--------

Unless otherwise noted, all the flags demonstrated can be combined with
each other.

`catsql example.sqlite`

Prints contents of entire database.  Suitable for small databases :-)

`catsql $DATABASE_URL --count`

Prints number of rows in each table of the database.  Suitable for medium
databases whose rows can be counted without too much pain.

`catsql $DATABASE_URL --limit 3`

Print 3 rows from every table in the database.  Suitable for medium
databases.

`catsql $DATABASE_URL --table users`

Print a single named table from the database.  When the table is specified,
a step of probing all tables in the database can be skipped, speeding things
up.

`catsql $DATABASE_URL --table users --id 20`

Print row(s) with column `id` (or any other name) equal to 20 in the
table called `users`. This is usable on large databases.  The `--id
20` filter can also be written as `--value id=20`. This form is useful
for columns whose name collides with another parameter of `catsql`.

`catsql $DATABASE_URL --color green`

Print row(s) with column `color` equal to `green` in any table.
On large databases, it would be a good idea to specify the table(s) to
look in, but on smaller databases it is convenient to let `catsql`
figure that out.  Tables without a column called `color` will be
omitted from search.

`catsql $DATABASE_URL --table users --grep paul`

Search all columns in the `users` table for the (case-insensitive)
sequence `paul`.  The search is done by a SQL query on the database
server, but is nevertheless a relatively expensive operation - best for
small to medium databases.

`catsql $DATABASE_URL --grep paul`

Search across the entire database - best for small databases :-).

`catsql $DATABASE_URL --grep paul --csv`

Output strictly in csv format, useful for piping into other tools
such as `csvlook` in the `csvkit` package.

`catsql $DATABASE_URL --sql "total < 1000"`

Return rows matching a SQL condition across entire database.  Tables for
whih the condition makes no sense are omitted.  Can be combined with
all other flags, such as specifying the table(s), column values, etc.

`catsql $DATABASE_URL --table users --grep paul --edit`

Edit whatever slice of the database you are viewing using your default
`$EDITOR`.  Only a single table can be edited at a time, since it is
edited strictly in CSV format, which is a single-table format.

`catsql $DATABASE_URL --column id,first_name`

Show just the `id` and `first_name` columns of any tables that have both
those columns.

Usage
-----

```
usage: catsql [-h] [--column COLUMN] [--count] [--csv] [--edit] [--grep GREP]
              [--limit LIMIT] [--load-bookmark] [--safe-null]
              [--save-bookmark SAVE_BOOKMARK] [--sql SQL] [--table TABLE]
              [--terse] [--value VALUE] [--verbose]
              catsql_database_url

Quickly display and edit a slice of a database.

positional arguments:
  catsql_database_url   Database url or filename. Examples: sqlite:///data.db,
                        mysql://user:pass@host/db,
                        postgres[ql]://user:pass@host/db, data.sqlite3

optional arguments:
  -h, --help            show this help message and exit
  --column COLUMN       Column to include (defaults to all columns). Can be a
                        comma separated list of multiple columns.
  --count               Show row counts instead of actual data.
  --csv                 Output strictly in CSV format.
  --edit                Edit original table in your favorite editor. Respects
                        $EDITOR environment variable.
  --grep GREP           Search cells for occurrence of a text fragment.
                        Translated to SQL query, performed by database.
  --limit LIMIT         Maximum number of rows per table.
  --load-bookmark       Load a set of filters from a file.
  --safe-null           Encode nulls in a reversible way.
  --save-bookmark SAVE_BOOKMARK
                        Save the current set of filters specified to a file.
  --sql SQL             Add a raw SQL filter for rows to include. Example:
                        "total < 1000", "created_at > now() - interval '1
                        day'". Tables that don't have the columns mentioned
                        are omitted.
  --table TABLE         Table to include (defaults to all tables). Can be a
                        comma separated list of multiple tables.
  --terse               Hide any columns with predetermined values.
  --value VALUE         Add a column=value filter. Example:
                          --value id=ID --value name=Jupiter
                        As a shortcut you can also do:
                          --id ID --name Jupiter
  --verbose             Show raw SQL queries as they are made.
```

License
-------

MIT
