import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM069(ExhaustiveTestCase):
    SOURCE_CODE = 'match x:\n    case 1:\n        try:\n            x = risky()\n        except ValueError:\n            x = 0\n        except TypeError:\n            x = -1\n    case _:\n        x = 0'
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
