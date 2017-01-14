from catsql.main import catsql
import unittest2

from tests.workspace import Workspace


class TestCommands(unittest2.TestCase):

    def setUp(self):
        self.workspace = Workspace(__file__)

    def tearDown(self):
        self.workspace.tearDown()

    def test_basic(self):
        catsql([self.workspace.number_db, "--output", self.workspace.output_file])
        assert self.workspace.output_lines() == 8

    def test_csv_output(self):
        catsql([self.workspace.number_db, "--output", self.workspace.output_file, "--csv"])
        assert self.workspace.output_lines() == 6
        assert len(self.workspace.output_rows()) == 5

    def test_column_value(self):
        catsql([self.workspace.number_db, "--NAME", "one", "--output", self.workspace.output_file, "--csv"])
        assert self.workspace.output_lines() == 2
        result = self.workspace.output_rows()
        assert len(result) == 1
        result = result[0]
        assert result['NAME'] == 'one'
        assert result['DIGIT'] == '1'

    def test_row_condition(self):
        catsql([self.workspace.number_db, "--sql", "NAME = 'one' or NAME = 'two'",
                "--output", self.workspace.output_file, "--csv"])
        result = self.workspace.output_rows()
        assert len(result) == 2
        assert result[0]['NAME'] == 'one'
        assert result[1]['NAME'] == 'two'

    def test_grep(self):
        catsql([self.workspace.number_db, "--grep", "three",
                "--output", self.workspace.output_file, "--csv"])
        result = self.workspace.output_rows()
        assert len(result) == 1
        assert result[0]['DIGIT'] == '3'

    def test_json_basic(self):
        catsql([self.workspace.number_db, "--json", self.workspace.output_file])
        result = self.workspace.output_json()
        assert result['count'] == 5

    def test_json_filtered(self):
        catsql([self.workspace.number_db, "--column", "DIGIT",
                "--json", self.workspace.output_file])
        result = self.workspace.output_json()
        assert result['count'] == 5

    def test_types(self):
        catsql([self.workspace.number_db, "--types", "--json", self.workspace.output_file])
        result = self.workspace.output_json()
        assert result['results'][0]['DIGIT'] == 'INTEGER'

    def test_sqlite_basic(self):
        catsql([self.workspace.number_db, "--sqlite", self.workspace.output_file_sql])
        catsql([self.workspace.output_file_sql, "--json", self.workspace.output_file])
        result = self.workspace.output_json()
        assert result['count'] == 5

    def test_excel_basic(self):
        catsql([self.workspace.number_db, "--excel", self.workspace.output_file_excel])
        result = self.workspace.output_excel()
        assert len(list(result.active)) == 5 + 1

    def test_terse_kv(self):
        catsql([self.workspace.number_db, "--terse",
                "--value", "DIGIT=4",
                "--json", self.workspace.output_file])
        result = self.workspace.output_json()
        assert result['count'] == 1
        assert 'NAME' in result['results'][0]
        assert 'DIGIT' not in result['results'][0]

    def test_terse_direct(self):
        catsql([self.workspace.number_db, "--terse",
                "--DIGIT", "4",
                "--json", self.workspace.output_file])
        result = self.workspace.output_json()
        assert result['count'] == 1
        assert 'NAME' in result['results'][0]
        assert 'DIGIT' not in result['results'][0]
