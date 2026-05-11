import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM074(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case 1:\n        y = [i for i in range(5) if i > 2]\n    case _:\n        y = []'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
