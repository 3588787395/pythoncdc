import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM048(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case Point(x=1, y=2) | Point(x=2, y=1):\n        y = 1\n    case _:\n        y = 0'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
