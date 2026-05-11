import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE02NestedTernary_a(ExhaustiveTestCase):
    SOURCE_CODE = """def f(a, b, c):
    x = "positive" if a > 0 else ("negative" if a < 0 else "zero")
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
