import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE01BasicTernary_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x, y):
    value = x if x >= 0 else y
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
