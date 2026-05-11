import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW082(ExhaustiveTestCase):
    SOURCE_CODE = "with open('a') as f1, open('b') as f2:\n    raise ValueError"
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
