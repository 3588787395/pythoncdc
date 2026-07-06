import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary03InExpr(ExhaustiveTestCase):
    SOURCE_CODE = """x = (a if flag else b) + 1"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
