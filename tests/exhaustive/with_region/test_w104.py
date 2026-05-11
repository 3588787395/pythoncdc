import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW104(ExhaustiveTestCase):
    SOURCE_CODE = 'def f():\n    with ctx:\n        x = 1\n        return x'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
