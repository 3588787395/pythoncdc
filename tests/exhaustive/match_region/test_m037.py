import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM037(ExhaustiveTestCase):
    SOURCE_CODE = "match x:\n    case {'name': name, **rest}:\n        y = name\n    case _:\n        y = ''"
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()
