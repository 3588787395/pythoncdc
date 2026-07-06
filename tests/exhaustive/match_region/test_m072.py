import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM072(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case 1:\n        i = 0\n        while i < 5:\n            i += 1\n    case _:\n        i = 0'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
