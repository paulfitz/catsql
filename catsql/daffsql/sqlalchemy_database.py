import daff
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import create_session
from sqlalchemy.exc import CompileError
from sqlalchemy.ext.declarative import declarative_base

from catsql.database import Database
from catsql.daffsql.sqlalchemy_helper import SqlAlchemyHelper


class SqlAlchemyDatabase(daff.SqlDatabase):

    def __init__(self, url):
        if isinstance(url, Database):
            db = url
            self.database = db
            self.url = db.url
            self.Base = db.Base
            self.engine = db.engine
            self.session = db._session
        else:
            self.database = None
            self.url = url
            self.Base = declarative_base()
            self.engine = create_engine(url)
            self.Base.metadata.reflect(self.engine)
            self.session = create_session(bind=self.engine)
        self.helper = SqlAlchemyHelper()

    def finalize(self):
        if self.database:
            changes = (self.helper.updates +
                       self.helper.inserts +
                       self.helper.deletes)
            self.database.finalize(changes > 0)

    def getTable(self, name):
        self.getColumns(name)
        result = self.Base.metadata.tables[name.toString()]
        return result

    @property
    def events(self):
        return {
            'updates': self.helper.updates,
            'inserts': self.helper.inserts,
            'deletes': self.helper.deletes,
            'skips': self.helper.skips
        }

    # needed because pragmas do not support bound parameters
    def getQuotedColumnName(self, name):
        return name  # adequate for test, not real life

    # needed because pragmas do not support bound parameters
    def getQuotedTableName(self, name):
        return name.toString()  # adequate for test, not real life

    def getColumns(self, name):
        name = name.toString()
        tab = self.Base.metadata.tables[name]
        columns = []
        for name, col in tab.columns.items():
            column = daff.SqlColumn()
            column.setName(name)
            column.setPrimaryKey(col.primary_key)
            try:
                type_name = str(col.type)
                if isinstance(col.type, sqlalchemy.types.Float):
                    type_name = 'REAL'
                column.setType(type_name, 'sqlalchemy')
            except CompileError:
                column.setType("", 'sqlalchemy')
            columns.append(column)
        return columns

    def begin(self, query, args=[], order=[]):
        print("Not implemented " + query)
        return False

    def beginRow(self, tab, row, order=[]):
        print("Not implemented")
        return False

    def read(self):
        return False

    def get(self, index):
        return None

    def end(self):
        pass

    def rowid(self):
        return "rowid"

    def getHelper(self):
        return self.helper

    def getNameForAttachment(self):
        return None
