import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW073(ExhaustiveTestCase):
    SOURCE_CODE = "with open('f') as f:\n    for i, line in enumerate(f):\n        x = i"
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
