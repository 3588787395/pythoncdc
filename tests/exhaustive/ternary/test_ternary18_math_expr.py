import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary18MathExpr(ExhaustiveTestCase):
    SOURCE_CODE = """result = base * (multiplier if scale else 1) + offset"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
