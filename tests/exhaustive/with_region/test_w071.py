import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW071(ExhaustiveTestCase):
    SOURCE_CODE = 'with ctx1 as c1:\n    with ctx2 as c2:\n        x = c1.value + c2.value'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
