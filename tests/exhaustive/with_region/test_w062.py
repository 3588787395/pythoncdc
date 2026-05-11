import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW062(ExhaustiveTestCase):
    SOURCE_CODE = "with open('f', 'rb') as f:\n    data = f.read()"
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
