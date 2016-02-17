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
usage: catsql [-h] [--table [TABLE [TABLE ...]]] [--row [ROW [ROW ...]]]
              [--context [CONTEXT [CONTEXT ...]]] [--hide-context] [--count]
              [--csv] [--save-bookmark SAVE_BOOKMARK] [--load-bookmark]
              [--edit] [--safe-null]
              url

Quickly display (part of) a database.

positional arguments:
  url                   Database url or filename. Examples: sqlite:///data.db,
                        mysql://user:pass@host/db,
                        postgres[ql]://user:pass@host/db, data.sqlite3

optional arguments:
  -h, --help            show this help message and exit
  --table [TABLE [TABLE ...]]
                        Tables to include (defaults to all tables)
  --row [ROW [ROW ...]]
                        Filters for rows to include. Examples: "total < 1000",
                        "name = 'american_bison'". Tables that don't have the
                        columns mentioned are omitted.
  --context [CONTEXT [CONTEXT ...]]
                        key=value filters
  --hide-context        Hide any columns mentioned in context filters
  --count               Show row counts instead of actual data.
  --csv                 Output strictly in CSV format.
  --save-bookmark SAVE_BOOKMARK
                        File to save link information in
  --load-bookmark       File to load link information from
  --edit                Edit original table in your favorite editor (multiple
                        tables not yet supported)
  --safe-null           Encode nulls in a reversible way
```

License
-------

MIT
