import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE099(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    x = 1\nexcept TypeError:\n    y = 2\nexcept ValueError:\n    z = 3\nelse:\n    w = 4\nfinally:\n    v = 5'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
