import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE043(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    x = [i for i in range(10)]\nexcept:\n    x = []'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
