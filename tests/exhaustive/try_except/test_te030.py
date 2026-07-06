import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE030(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    try:\n        x = 1\n    except TypeError:\n        y = 2\nexcept:\n    z = 3'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
