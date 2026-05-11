import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE02NestedTernary_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(a, b, c):
    result = a if a > b else (b if b > c else c)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
