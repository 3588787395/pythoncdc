import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestTE044(ExhaustiveTestCase):
    SOURCE_CODE = 'try:\n    x = {k: v for k, v in {}.items()}\nexcept:\n    x = {}'
    REGION_TYPE = "TRY_EXCEPT"
    def test_decompile(self):
        self.verify_decompilation()
