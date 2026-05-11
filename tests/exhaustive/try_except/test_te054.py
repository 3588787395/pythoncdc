import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE054(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    x = 1\nexcept ValueError as e:\n    raise RuntimeError from e'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
