import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE024(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    x = 1\nexcept:\n    y = 2\nfinally:\n    cleanup = True'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
