import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary16DoubleNested(ExhaustiveTestCase):
    SOURCE_CODE = """x = (a if p1 else (b if p2 else c)) if p3 else d"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
