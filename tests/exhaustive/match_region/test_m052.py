import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM052(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case 1:\n        for i in range(3):\n            print(i)\n    case _:\n        pass'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
