import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM054(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case 1:\n        try:\n            y = 1\n        except:\n            z = 2\n    case _:\n        pass'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
