import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE042(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    i = 0\n    while i < 10:\n        i += 1\nexcept:\n    i = 0'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
