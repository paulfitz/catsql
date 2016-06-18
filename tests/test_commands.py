import argparse
from catsql.main import catsql
from catsql.cmdline import add_options
import csv
import os
import re
import six
import shutil
import sqlite3
import unittest2

NUMBERS_SQL = """
BEGIN TRANSACTION;
CREATE TABLE sheet (NAME PRIMARY KEY,DIGIT INTEGER);
INSERT INTO "sheet" VALUES('one',1);
INSERT INTO "sheet" VALUES('two',2);
INSERT INTO "sheet" VALUES('thrEE',3);
INSERT INTO "sheet" VALUES('foUR',4);
INSERT INTO "sheet" VALUES('five',NULL);
COMMIT;
"""

def numbers(fname):
    conn = sqlite3.connect(fname)
    conn.cursor().executescript(NUMBERS_SQL)


class TestCommands(unittest2.TestCase):

    def setUp(self):
        self.work = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'tmp_data')
        os.makedirs(self.work)
        number_file = "{}/numbers.sqlite".format(self.work)
        numbers(number_file)
        self.number_db = 'sqlite:///{}'.format(number_file)
        self.output_file = "{}/output.txt".format(self.work)
        self.output_text_cache = None

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

    def tearDown(self):
        try:
            shutil.rmtree(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                       'tmp_data'))
        except OSError:
            pass

    def test_basic(self):
        catsql([self.number_db, "--output", self.output_file])
        assert self.output_lines() == 8

    def test_csv_output(self):
        catsql([self.number_db, "--output", self.output_file, "--csv"])
        assert self.output_lines() == 6
        assert len(self.output_rows()) == 5

    def test_column_value(self):
        catsql([self.number_db, "--NAME", "one", "--output", self.output_file, "--csv"])
        assert self.output_lines() == 2
        result = self.output_rows()
        assert len(result) == 1
        result = result[0]
        assert result['NAME'] == 'one'
        assert result['DIGIT'] == '1'

    def test_row_condition(self):
        catsql([self.number_db, "--sql", "NAME = 'one' or NAME = 'two'",
                "--output", self.output_file, "--csv"])
        result = self.output_rows()
        assert len(result) == 2
        assert result[0]['NAME'] == 'one'
        assert result[1]['NAME'] == 'two'

    def test_grep(self):
        catsql([self.number_db, "--grep", "three",
                "--output", self.output_file, "--csv"])
        result = self.output_rows()
        assert len(result) == 1
        assert result[0]['DIGIT'] == '3'
