import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM043(ExhaustiveTestCase):
    SOURCE_CODE = "match x:\n    case {'type': 'a', 'value': v}:\n        y = v\n    case {'type': 'b', 'value': v}:\n        y = -v\n    case _:\n        y = 0"
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
