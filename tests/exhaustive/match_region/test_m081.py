import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM081(ExhaustiveTestCase):
    SOURCE_CODE = '''match x:
    case 1 | 3 | 5 | 7 | 9:
        y = 'odd'
    case 2 | 4 | 6 | 8:
        y = 'even'
    case _:
        y = 'other'
'''
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
