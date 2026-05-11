import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE036(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    while True:\n        break\nexcept:\n    y = 1'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
