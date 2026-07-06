import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW024(ExhaustiveTestCase):
    SOURCE_CODE = "with open('a') as fa, open('b') as fb:\n    result = fa.read() + fb.read()"
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
