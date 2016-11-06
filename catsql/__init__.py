from catsql.database import Database


def connect(db, verbose=False, tables=None, columns=None):
    return Database(db, verbose=verbose, tables=tables).query(columns=columns)
