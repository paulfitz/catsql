catsql
======


Quickly display (part of) a database.  Thin wrapper around SQLAlchemy.
Pronounced "cat-skill" for some reason.

Installation
------------

`pip install catsql`

Examples
--------

 * `catsql example.sqlite`
 * `catsql postgres://foo:bar@thing.rds.amazonaws.com:5432/database`
 * `catsql example.sqlite --table users`
 * `catsql foo.csv --rows 'total < 1000'`

Usage
-----

```
usage: catsql [-h] [--table [TABLE [TABLE ...]]] [--row [ROW [ROW ...]]]
              [--bare] [--csv]
              url

Quickly display (part of) a database.

positional arguments:
  url                   Database url or filename. Examples: sqlite:///data.db,
                        mysql://user:pass@host/db,
                        postgres[ql]://user:pass@host/db, data.sqlite3,
                        data.csv

optional arguments:
  -h, --help            show this help message and exit
  --table [TABLE [TABLE ...]]
                        Tables to include (defaults to all tables)
  --row [ROW [ROW ...]]
                        Filters for rows to include. Examples: 'total < 1000',
                        'name = "american_bison"'. Tables that don't have the
                        columns mentioned are omitted.
  --bare                Show table and column names, skip actual data.
  --csv                 Output strictly in CSV format.
```

License
-------

MIT
