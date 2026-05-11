import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN08TernaryAssignNested_x_y(ExhaustiveTestCase):
    SOURCE_CODE = """x = 1 if y > 0 else 2 if y == 0 else 3"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
