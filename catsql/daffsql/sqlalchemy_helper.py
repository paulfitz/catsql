from __future__ import print_function
import daff
import json
import sys

from catsql.daffsql.dictify import dictify

class SqlAlchemyHelper(daff.SqlHelper):
    def __init__(self):
        self.updates = 0
        self.inserts = 0
        self.deletes = 0
        self.skips = 0

    def update(self, db, name, conds, vals):
        conds = dictify(conds)
        vals = dictify(vals)
        tab = db.getTable(name)

        # should work doesn't work :(
        #q = db.session.query(tab)
        #q = q.filter_by(**conds)
        #q = q.update(vals)

        q = db.getTable(name).update()
        for key, value in conds.items():
            q = q.where(tab.c[key] == value)
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
        q = db.getTable(name).delete()
        for key, value in conds.items():
            q = q.where(tab.c[key] == value)
        result = db.session.connection().execute(q)
        if result.rowcount == 0:
            print(" * skipped delete {}".format(json.dumps(conds)),
                  file=sys.stderr)
            self.skips += 1
        else:
            self.deletes += result.rowcount

    def insert(self, db, name, vals):
        vals = dictify(vals)
        tab = db.getTable(name)
        q = db.getTable(name).insert()
        q = q.values(vals)
        db.session.connection().execute(q)
        self.inserts += 1
