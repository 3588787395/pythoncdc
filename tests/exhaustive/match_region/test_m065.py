import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM065(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case 1:\n        if a > 0:\n            y = 1\n        elif a < 0:\n            y = -1\n        else:\n            y = 0\n    case _:\n        y = 0'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
