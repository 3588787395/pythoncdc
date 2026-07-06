import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE040(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    if a:\n        x = 1\n    elif b:\n        x = 2\n    else:\n        x = 3\nexcept:\n    x = 0'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
