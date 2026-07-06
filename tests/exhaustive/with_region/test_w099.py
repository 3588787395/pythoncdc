import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW099(ExhaustiveTestCase):
    SOURCE_CODE = 'with lock:\n    x = 0\n    for i in range(5):\n        x += i'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
