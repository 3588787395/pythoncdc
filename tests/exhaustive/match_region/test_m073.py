import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM073(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case 1:\n        y = {i: i * 2 for i in range(5)}\n    case _:\n        y = {}'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
