import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE03TernaryArith_a(ExhaustiveTestCase):
    SOURCE_CODE = """def f(a, b):
    result = (a + b) if a > 0 else (a * 2)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
