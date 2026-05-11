import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE013(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    a = 1\n    b = 2\n    c = a + b\nexcept:\n    d = 0'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
