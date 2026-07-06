import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE048(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    x = 1\n    if x > 0:\n        y = x * 2\n    else:\n        y = x * -1\nexcept:\n    y = 0'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
