import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN08TernaryAssignNested_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """n = 1 if m > 0 else 2 if m == 0 else 3"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
