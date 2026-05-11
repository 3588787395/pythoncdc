import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE050(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    for i in range(3):\n        try:\n            x = 1 / i\n        except ZeroDivisionError:\n            x = 0\nexcept:\n    x = -1'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
