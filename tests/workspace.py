import csv
import json
import openpyxl
import os
import re
import six
import shutil
import sqlite3

NUMBERS_SQL = """
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS {name} (NAME TEXT,DIGIT INTEGER);
INSERT INTO {name} VALUES('one',1);
INSERT INTO {name} VALUES('two',2);
INSERT INTO {name} VALUES('thrEE',3);
INSERT INTO {name} VALUES('foUR',4);
INSERT INTO {name} VALUES('five',NULL);
COMMIT;
"""

PRODUCT_SQL = """
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS product (DIGIT INTEGER PRIMARY KEY, CODE TEXT);
INSERT INTO "product" VALUES(1, '.');
INSERT INTO "product" VALUES(2, '..');
INSERT INTO "product" VALUES(3, '...');
COMMIT;
"""


class Workspace(object):

    def __init__(self, path):
        self.setUp(path)

    def numbers(self, fname, name='sheet'):
        conn = sqlite3.connect(fname)
        conn.cursor().executescript(NUMBERS_SQL.format(name=name))

    def setUp(self, path):
        self.path = path
        self.work = os.path.join(os.path.dirname(os.path.realpath(path)),
                                 'tmp_data')
        if not os.path.isdir(self.work):
            os.makedirs(self.work)
        self.number_file = "{}/numbers.sqlite".format(self.work)
        self.numbers(self.number_file)
        self.number_db = 'sqlite:///{}'.format(self.number_file)
        self.output_file = "{}/output.txt".format(self.work)
        self.output_file_sql = "{}/output.sqlite".format(self.work)
        self.output_file_excel = "{}/output.xlsx".format(self.work)
        self.output_text_cache = None

    def filename(self, partial_filename):
        return "{}/{}".format(self.work, partial_filename)

    def add_product_table(self):
        conn = sqlite3.connect(self.number_file)
        conn.cursor().executescript(PRODUCT_SQL)

    def tearDown(self):
        try:
            shutil.rmtree(os.path.join(os.path.dirname(os.path.realpath(self.path)),
                                       'tmp_data'))
        except OSError:
            pass

    def output_text(self):
        if self.output_text_cache:
            return self.output_text_cache
        with open(self.output_file, 'rt') as handle:
            self.output_text_cache = handle.read()
        return self.output_text_cache

    def output_lines(self):
        return len(re.findall('\n', self.output_text()))

    def output_rows(self):
        reader = csv.DictReader(six.StringIO(self.output_text()))
        return list(reader)

    def output_json(self):
        return json.loads(self.output_text())

    def output_excel(self):
        return openpyxl.load_workbook(filename=self.output_file_excel)
