import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW044(ExhaustiveTestCase):
    SOURCE_CODE = 'with ctx:\n    i = 0\n    while i < 10:\n        i += 1'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
