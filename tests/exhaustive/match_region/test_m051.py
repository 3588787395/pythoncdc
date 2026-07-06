import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM051(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case 1:\n        if y > 0:\n            z = 1\n    case _:\n        z = 0'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
