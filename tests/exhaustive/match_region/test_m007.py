import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM007(ExhaustiveTestCase):
    SOURCE_CODE = "match x:\n    case 0:\n        y = 'zero'\n    case 1:\n        y = 'one'\n    case _:\n        y = 'other'"
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
