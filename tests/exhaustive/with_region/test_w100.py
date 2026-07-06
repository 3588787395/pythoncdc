import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW100(ExhaustiveTestCase):
    SOURCE_CODE = 'with ctx:\n    x = []\n    for i in range(3):\n        x.append(i)'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
