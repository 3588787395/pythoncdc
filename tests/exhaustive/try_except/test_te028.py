import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE028(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    if x > 0:\n        y = 1\nexcept:\n    z = 2'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
