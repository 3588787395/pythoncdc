import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM097(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case (a, b) if a == b:\n        y = 1\n    case (a, b):\n        y = 0\n    case _:\n        y = -1'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
