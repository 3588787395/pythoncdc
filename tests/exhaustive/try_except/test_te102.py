import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE102(ExhaustiveTestCase):
    SOURCE_CODE = "try:\n    x = 1\nexcept (TypeError, ValueError) as e:\n    y = str(e)\nexcept KeyError:\n    y = 'key_error'"
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
