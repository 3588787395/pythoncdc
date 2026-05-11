import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW049(ExhaustiveTestCase):
    SOURCE_CODE = 'with ctx:\n    if a:\n        x = 1\n    elif b:\n        x = 2\n    else:\n        x = 3'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
