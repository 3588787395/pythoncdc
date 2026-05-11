import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN04NestedTernary_x(ExhaustiveTestCase):
    SOURCE_CODE = """'a' if x > 0 else 'b' if x == 0 else 'c'"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
