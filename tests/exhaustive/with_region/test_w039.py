import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW039(ExhaustiveTestCase):
    SOURCE_CODE = 'with ctx:\n    for i in range(3):\n        for j in range(3):\n            x = i + j'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
