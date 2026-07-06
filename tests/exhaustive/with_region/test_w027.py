import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW027(ExhaustiveTestCase):
    SOURCE_CODE = "with open('f') as f:\n    for line in f:\n        print(line)"
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
