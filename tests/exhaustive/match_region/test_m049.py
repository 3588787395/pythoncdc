import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM049(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case n if n > 10:\n        y = 3\n    case n if n > 5:\n        y = 2\n    case n if n > 0:\n        y = 1\n    case _:\n        y = 0'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
