import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE019(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    x = 1\nexcept TypeError:\n    x = 0\nexcept ValueError:\n    x = -1\nexcept RuntimeError:\n    x = -2'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
