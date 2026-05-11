import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW059(ExhaustiveTestCase):
    SOURCE_CODE = "with open('f', 'r') as f:\n    x = f.readlines()"
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
