import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary05Chained(ExhaustiveTestCase):
    SOURCE_CODE = """x = a if c1 else b if c2 else d if c3 else e"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
