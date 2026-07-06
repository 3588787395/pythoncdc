import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE096(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    x = 1\n    y = 2\nexcept:\n    x = 0\n    y = 0'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
