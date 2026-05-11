import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE014(ExhaustiveTestCase):
    SOURCE_CODE = "try:\n    x = {}\n    y = x['key']\nexcept KeyError:\n    y = None"
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
