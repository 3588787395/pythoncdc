import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW017(ExhaustiveTestCase):
    SOURCE_CODE = "with open('f') as f:\n    x = f.readline()"
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
