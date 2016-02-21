catsql
======


Quickly display (part of) a database.  Thin wrapper around SQLAlchemy.
Pronounced "cat-skill" for some reason.

Installation
------------

`pip install catsql`

Demo
----

Please excuse the uneven pacing :-)

![Terminal demo](https://cloud.githubusercontent.com/assets/118367/13099641/551dd062-d502-11e5-87ff-422d3d275005.gif)

Examples
--------

 * `catsql example.sqlite`
 * `catsql postgres://foo:bar@thing.rds.amazonaws.com:5432/database`
 * `catsql example.sqlite --table users`
 * `catsql $DATABASE_URL --table users --edit` - edit your database, I
   know, why does `cat` have an editor, there are good^H^H^H^H reasons believe
   me.

Usage
-----

```
usage: catsql [-h] [--count] [--csv] [--edit] [--grep GREP] [--limit LIMIT]
              [--load-bookmark] [--safe-null] [--save-bookmark SAVE_BOOKMARK]
              [--sql SQL] [--table TABLE] [--terse] [--value VALUE]
              [--verbose]
              url

Quickly display and edit a slice of a database.

positional arguments:
  url                   Database url or filename. Examples: sqlite:///data.db,
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
  --value VALUE         Add a column=value filter. Translated to SQL,
                        filtering done by database.
  --verbose             Show raw SQL queries as they are made.
```

License
-------

MIT
