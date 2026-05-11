import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE03TernaryArith_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x, y, z):
    val = (x ** 2) if y > z else (y * z)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
