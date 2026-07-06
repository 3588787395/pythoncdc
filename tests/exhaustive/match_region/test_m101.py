import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM101(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case Point(x=x, y=y) if x > 0 and y > 0:\n        z = 1\n    case Point(x=x, y=y):\n        z = 0\n    case _:\n        z = -1'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
