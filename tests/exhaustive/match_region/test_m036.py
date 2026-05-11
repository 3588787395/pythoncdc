import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM036(ExhaustiveTestCase):
    SOURCE_CODE = "match x:\n    case {'x': x_val, 'y': y_val}:\n        z = x_val + y_val\n    case _:\n        z = 0"
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
