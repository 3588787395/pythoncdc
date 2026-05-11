import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM019(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case 1:\n        y = 10\n    case 2:\n        y = 20\n    case 3:\n        y = 30\n    case 4:\n        y = 40\n    case _:\n        y = 0'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
