import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM014(ExhaustiveTestCase):
    SOURCE_CODE = "match x:\n    case 1:\n        y = 'a'\n    case 2:\n        y = 'b'"
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
