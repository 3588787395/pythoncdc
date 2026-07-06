import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE01BasicTernary_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(s1, s2):
    result = s1 if s1 else s2
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
