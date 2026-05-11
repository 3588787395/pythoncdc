import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE021(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    x = 1\nexcept TypeError as e:\n    y = 1\nexcept ValueError as e:\n    y = 2\nexcept:\n    y = 3'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
