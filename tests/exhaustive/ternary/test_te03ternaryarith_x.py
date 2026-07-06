import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE03TernaryWithArith_n(ExhaustiveTestCase):
    SOURCE_CODE = """value = x * 2 if x > 0 else x + 10"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
