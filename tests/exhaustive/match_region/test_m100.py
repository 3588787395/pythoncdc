import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM100(ExhaustiveTestCase):
    SOURCE_CODE = "match x:\n    case {'a': 1, **rest}:\n        y = rest\n    case _:\n        y = {}"
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
