import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM066(ExhaustiveTestCase):
    SOURCE_CODE = "def f():\n    match x:\n        case 1:\n            return 'one'\n        case 2:\n            return 'two'\n        case _:\n            return 'other'"
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
