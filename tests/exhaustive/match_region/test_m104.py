import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM104(ExhaustiveTestCase):
    SOURCE_CODE = "match x:\n    case {'x': x_val}:\n        y = x_val\n    case {'y': y_val}:\n        y = y_val\n    case _:\n        y = 0"
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
