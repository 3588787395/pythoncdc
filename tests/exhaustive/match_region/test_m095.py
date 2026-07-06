import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM095(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case 1 | 2 | 3:\n        y = 1\n    case 4 | 5 | 6:\n        y = 2\n    case _:\n        y = 0'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
