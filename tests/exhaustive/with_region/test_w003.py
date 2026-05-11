import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW003(ExhaustiveTestCase):
    SOURCE_CODE = "with open('a') as f1, open('b') as f2:\n    x = f1.read() + f2.read()"
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
