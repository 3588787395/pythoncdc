import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE047(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    for i in range(3):\n        if i == 1:\n            continue\n        x = i\nexcept:\n    x = 0'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
