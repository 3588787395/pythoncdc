import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE091(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    x = 1\nexcept:\n    y = 2\nelse:\n    pass\nfinally:\n    pass'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
