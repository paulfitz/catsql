catsql
======


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

 * `catsql example.sqlite --limit 3`
 * `catsql $DATABASE_URL --table users --id 20`
 * `catsql $DATABASE_URL --table users --grep paul`
 * `catsql $DATABASE_URL --table users --grep paul --edit` - edit whatever
   slice of the database you are viewing using your default `$EDITOR`.
 * `catsql postgres://foo:bar@thing.rds.amazonaws.com:5432/database` - if
   you install the appropriate SqlAlchemy drivers, you can edit postgres,
   mysql, ... databases in your default `$EDITOR`.

Usage
-----

```
usage: catsql [-h] [--count] [--csv] [--edit] [--grep GREP] [--limit LIMIT]
              [--load-bookmark] [--safe-null] [--save-bookmark SAVE_BOOKMARK]
              [--sql SQL] [--table TABLE] [--terse] [--value VALUE]
              [--verbose]
              catsql_database_url

Quickly display and edit a slice of a database.

positional arguments:
  catsql_database_url   Database url or filename. Examples: sqlite:///data.db,
                        mysql://user:pass@host/db,
                        postgres[ql]://user:pass@host/db, data.sqlite3

optional arguments:
  -h, --help            show this help message and exit
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
  --sql SQL             Add a SQL filter for rows to include. Examples: "total
                        < 1000", "name = 'american_bison'". Tables that don't
                        have the columns mentioned are omitted.
  --table TABLE         Table to include (defaults to all tables)
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
