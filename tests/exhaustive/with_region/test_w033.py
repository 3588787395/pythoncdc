import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW033(ExhaustiveTestCase):
    SOURCE_CODE = 'with lock:\n    for i in range(10):\n        shared += 1'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
