from __future__ import unicode_literals

import catsql
import json
import unittest2

from tests.workspace import Workspace

class TestLibrary(unittest2.TestCase):

    def setUp(self):
        self.workspace = Workspace(__file__)

    def tearDown(self):
        self.workspace.tearDown()

    def test_order(self):
        q = catsql.connect(self.workspace.number_db)
        q.order(['NAME'])
        self.assertEquals(len(q), 1)
        self.assertEquals(q.rows[0].NAME, 'five')

    def test_limit(self):
        q = catsql.connect(self.workspace.number_db)
        q.limit(2)
        self.assertEquals(len(q), 1)
        self.assertEquals(len(q.rows.all()), 2)

    def test_grep(self):
        q = catsql.connect(self.workspace.number_db)
        q.grep('wo')
        self.assertEquals(len(q), 1)
        self.assertEquals(len(q.rows.all()), 1)
        self.assertEquals(q.row.NAME, 'two')

    def test_where_sql(self):
        q = catsql.connect(self.workspace.number_db)
        q.where_sql('DIGIT = 2')
        self.assertEquals(len(q), 1)
        self.assertEquals(len(q[0]['rows'].all()), 1)
        self.assertEquals(q.row.NAME, 'two')

    def test_where_sqls(self):
        q = catsql.connect(self.workspace.number_db)
        q.where_sqls(['DIGIT > 2', 'NAME like "%o%"'])
        self.assertEquals(len(q), 1)
        self.assertEquals(len(q[0]['rows'].all()), 1)
        self.assertEquals(q.row.DIGIT, 4)

    def test_where_kv(self):
        q = catsql.connect(self.workspace.number_db)
        q.where_kv({ 'DIGIT': 4 })
        self.assertEquals(len(q), 1)
        self.assertEquals(len(q[0]['rows'].all()), 1)
        self.assertEquals(q.row.DIGIT, 4)
        
    def test_where_kv_with_expansion(self):
        q = catsql.connect(self.workspace.number_db)
        digits = [
            {
                'DIGIT': 2,
            },
            {
                'DIGIT': 3
            }
        ]
        fname = self.workspace.filename('digit.txt')
        json.dump(digits, open(fname, 'w'))
        q.where_kv_with_expansion({ 'DIGIT': '@{}'.format(fname) })
        q.order(['DIGIT'])
        self.assertEquals(len(q), 1)
        self.assertEquals(len(q.rows.all()), 2)
        self.assertEquals(q.rows[0].DIGIT, 2)
        self.assertEquals(q.rows[1].DIGIT, 3)
        
    def test_distinct(self):
        self.workspace.numbers(self.workspace.number_file) # add duplicates
        q = catsql.connect(self.workspace.number_db)
        self.assertEquals(len(q), 1)
        self.assertEquals(len(q.rows.all()), 10)
        q.distinct()
        self.assertEquals(len(q.rows.all()), 5)

    def test_connect_column(self):
        q = catsql.connect(self.workspace.number_db, columns=['NAME'])
        q.order()
        self.assertEquals(len(q), 1)
        self.assertEquals(len(q.rows.all()), 5)
        self.assertEquals(q.rows[0].NAME, 'five')
        with self.assertRaises(AttributeError):
            print(q.rows[0].DIGIT)

    def test_connect_table(self):
        self.workspace.numbers(self.workspace.number_file, 'more')
        q = catsql.connect(self.workspace.number_db)
        self.assertEquals(len(q), 2)
        q = catsql.connect(self.workspace.number_db, tables=['more'])
        self.assertEquals(len(q), 1)

    def test_where_kv_multiple_tables(self):
        self.workspace.add_product_table()
        q = catsql.connect(self.workspace.number_db)
        q.where_kv({ 'CODE': '.' })
        self.assertEquals(len(q), 1)

    def test_where_kv_with_expansion_multiple_tables(self):
        self.workspace.add_product_table()
        q = catsql.connect(self.workspace.number_db)
        codes = [
            {
                'CODE': '.',
            },
            {
                'CODE': '..'
            }
        ]
        fname = self.workspace.filename('code.txt')
        json.dump(codes, open(fname, 'w'))
        q.where_kv_with_expansion({ 'CODE': '@{}'.format(fname) })
        q.order(['CODE'])
        self.assertEquals(len(q), 1)
        self.assertEquals(len(q.rows.all()), 2)

    def test_where_sql_multiple_tables(self):
        self.workspace.add_product_table()
        q = catsql.connect(self.workspace.number_db)
        q.where_sql('CODE = "."')
        self.assertEquals(len(q), 1)

