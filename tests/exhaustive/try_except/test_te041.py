import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE041(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    d = {}\n    for k in d:\n        v = d[k]\nexcept:\n    v = None'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
