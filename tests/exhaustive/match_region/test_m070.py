import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM070(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case 1:\n        with ctx:\n            y = 1\n            z = 2\n    case _:\n        y = z = 0'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
