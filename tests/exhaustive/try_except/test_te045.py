import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE045(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    if x and y:\n        z = 1\nexcept:\n    z = 0'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
