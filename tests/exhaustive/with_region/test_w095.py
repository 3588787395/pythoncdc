import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW095(ExhaustiveTestCase):
    SOURCE_CODE = 'with ctx:\n    for i in range(1):\n        pass'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
