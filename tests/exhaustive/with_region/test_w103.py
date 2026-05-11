import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW103(ExhaustiveTestCase):
    SOURCE_CODE = "with open('a') as fa, open('b') as fb:\n    x = fa.read()\n    y = fb.read()\n    z = x + y"
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
