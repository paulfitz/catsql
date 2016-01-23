#!/usr/bin/env python

from sqlalchemy import *
from sqlalchemy.orm import create_session, mapper
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.declarative import declarative_base
import sys

def main():

    url = sys.argv[1]

    Base = declarative_base()
    try:
        engine = create_engine(url)
    except ArgumentError:
        import magic
        result = magic.from_file(url).lower()
        if 'sqlite' in result:
            url = 'sqlite:///' + url
            engine = create_engine(url)
        elif 'text' in result:
            import csv
            engine = create_engine('sqlite://')
            with open(url) as f:
                table = None
                metadata = MetaData(bind=engine)
                cf = csv.DictReader(f, delimiter=',')
                for row in cf:
                    if table is None:
                        table = Table('_chancer_table_', metadata, 
                                      Column('_chancer_id_', Integer, primary_key=True),
                                      *(Column(rowname, String()) for rowname in row.keys()))
                        table.create()
                    table.insert().values(**row).execute()

                class CsvTable(object): pass
                mapper(CsvTable, table)
        else:
            engine = create_engine(url)

    Base.metadata.reflect(engine)

    session = create_session(bind=engine)

    for idx, (table_name, table) in enumerate(Base.metadata.tables.items()):
        if idx > 0:
            print ""
        if table_name != '_chancer_table_':
            print table_name
            print '=' * len(table_name)
        columns = table.columns.keys()
        header = ",".join(column for column in columns if column != '_chancer_id_')
        print header
        print '-' * len(header)
        for row in session.query(table):
            print ",".join(str(cell) for c, cell in enumerate(row) if columns[c] != '_chancer_id_')

if __name__ == "__main__":
    main()
