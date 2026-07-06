import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM102(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case 1:\n        a = 1\n    case 2:\n        b = 2\n    case 3:\n        c = 3\n    case 4:\n        d = 4\n    case 5:\n        e = 5\n    case _:\n        z = 0'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
