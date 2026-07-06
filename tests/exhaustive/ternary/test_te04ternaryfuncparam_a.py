import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE04TernaryFuncParam_a(ExhaustiveTestCase):
    SOURCE_CODE = """def f(a, b):
    print("max" if a > b else "min", a if a > 0 else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
