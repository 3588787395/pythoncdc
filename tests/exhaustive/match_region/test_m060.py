import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM060(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case [a, b]:\n        y = a + b\n        z = a * b\n    case _:\n        y = z = 0'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
