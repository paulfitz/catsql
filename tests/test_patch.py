from catsql.main import catsql
from catsql.patch import patchsql
import unittest2

from tests.workspace import Workspace


class TestLibrary(unittest2.TestCase):

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
