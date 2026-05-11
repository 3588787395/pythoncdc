import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE062(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    x = 1\nexcept (TypeError, ValueError) as e:\n    y = str(e)'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
