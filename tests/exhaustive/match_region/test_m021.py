import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM021(ExhaustiveTestCase):
    SOURCE_CODE = "match x:\n    case 'start':\n        y = 1\n    case 'stop':\n        y = 2\n    case 'pause':\n        y = 3\n    case _:\n        y = 0"
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
