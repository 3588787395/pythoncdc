import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE012(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    x = 1\nexcept:\n    y = 2\nelse:\n    w = 3\nfinally:\n    z = 4'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
