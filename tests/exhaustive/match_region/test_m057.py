import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM057(ExhaustiveTestCase):
    SOURCE_CODE = 'def f():\n    match x:\n        case 1:\n            return 1\n        case _:\n            return 0'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
