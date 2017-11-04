from catsql.main import catsql
from catsql.patch import patchsql
import mock
import unittest

from tests.workspace import Workspace


def editor_call(args):

    filename = args[1]
    with open(filename, 'r') as fin:
        txt = fin.read()
    txt = txt.replace('2', '22')
    with open(filename, 'w') as fout:
        fout.write(txt)


class TestPatch(unittest.TestCase):

    def setUp(self):
        self.workspace = Workspace(__file__)

    def tearDown(self):
        self.workspace.tearDown()

    def test_basic(self):
        patch = self.workspace.filename('patch.diff')
        with open(patch, 'w') as fout:
            fout.write("@@,NAME,DIGIT\n"
                       "->,two,2->22\n")
        patchsql([self.workspace.number_db, '--table', 'sheet', '--patch', patch])
        catsql([self.workspace.number_db, "--json", self.workspace.output_file,
                '--NAME', 'two'])
        result = self.workspace.output_json()
        self.assertEquals(len(result['results']), 1)
        self.assertEquals(result['results'][0]['DIGIT'], 22)

    def test_from_file_pair(self):
        f1 = self.workspace.filename('f1.csv')
        f2 = self.workspace.filename('f2.csv')
        with open(f1, 'w') as fout:
            fout.write("NAME,DIGIT\n"
                       "two,2\n")
        with open(f2, 'w') as fout:
            fout.write("NAME,DIGIT\n"
                       "two,22\n")
        patchsql([self.workspace.number_db, '--table', 'sheet', '--follow', f1, f2,
                  '--quiet'])
        catsql([self.workspace.number_db, "--json", self.workspace.output_file,
                '--NAME', 'two'])
        result = self.workspace.output_json()
        self.assertEquals(len(result['results']), 1)
        self.assertEquals(result['results'][0]['DIGIT'], 22)

    @mock.patch('catsql.main.call', editor_call)
    def test_integrated(self):
        catsql([self.workspace.number_db, '--edit', '--quiet'])
        catsql([self.workspace.number_db, "--json", self.workspace.output_file,
                '--NAME', 'two'])
        result = self.workspace.output_json()
        self.assertEquals(len(result['results']), 1)
        self.assertEquals(result['results'][0]['DIGIT'], 22)
