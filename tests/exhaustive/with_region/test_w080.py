import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW080(ExhaustiveTestCase):
    SOURCE_CODE = 'for i in range(3):\n    with ctx:\n        if i < 1:\n            continue'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
