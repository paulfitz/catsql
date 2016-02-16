from __future__ import print_function
import daff
import json
import sys

from catsql.daffsql.dictify import dictify

EPSILON = 0.00001

class SqlAlchemyHelper(daff.SqlHelper):
    def __init__(self):
        self.updates = 0
        self.inserts = 0
        self.deletes = 0
        self.skips = 0
        self.cached_columns = {}

    def getColumns(self, db, name):
        if name in self.cached_columns:
            return self.cached_columns[name]
        columns = db.getColumns(name)
        record = self.cached_columns[name] = {}
        for column in columns:
            record[column.name] = {
                'float': column.type_value == 'REAL',
                'blank': column.type_value == '',
                'primary': column.primary
            }
        return record

    def where(self, q, key, value, tab, columns):
        is_float = columns[key]['float']
        if not is_float:
            if columns[key]['blank']:
                # could be sqlite untyped
                try:
                    if '.' in value:
                        x = float(value)
                        is_float = True
                except:
                    pass
        if is_float:
            # use epsilon
            q = q.where(tab.c[key] > float(value) - EPSILON)
            q = q.where(tab.c[key] < float(value) + EPSILON)
        else:
            q = q.where(tab.c[key] == value)
        return q

    def update(self, db, name, conds, vals):
        conds = dictify(conds)
        vals = dictify(vals)
        tab = db.getTable(name)
        columns = self.getColumns(db, name)

        # should work doesn't work :(
        #q = db.session.query(tab)
        #q = q.filter_by(**conds)
        #q = q.update(vals)

        q = db.getTable(name).update()
        for key, value in conds.items():
            q = self.where(q, key, value, tab, columns)
        q = q.values(vals)
        result = db.session.connection().execute(q)
        if result.rowcount == 0:
            print(" * skipped update {}".format(json.dumps(conds)),
                  file=sys.stderr)
            self.skips += 1
        else:
            self.updates += result.rowcount

    def delete(self, db, name, conds):
        conds = dictify(conds)
        tab = db.getTable(name)
        columns = self.getColumns(db, name)
        q = db.getTable(name).delete()
        for key, value in conds.items():
            q = self.where(q, key, value, tab, columns)
        result = db.session.connection().execute(q)
        if result.rowcount == 0:
            print(" * skipped delete {}".format(json.dumps(conds)),
                  file=sys.stderr)
            self.skips += 1
        else:
            self.deletes += result.rowcount

    def insert(self, db, name, vals):
        columns = self.getColumns(db, name)
        vals = dictify(vals)
        keys = vals.keys()
        for key in keys:
            if vals[key] == '':
                if columns[key]['primary']:
                    # don't try to set blank primary keys, assume they are autoincrement
                    vals.pop(key)
        tab = db.getTable(name)
        q = db.getTable(name).insert()
        q = q.values(vals)
        db.session.connection().execute(q)
        self.inserts += 1
