import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE07TernaryWithBoolOp(ExhaustiveTestCase):
    SOURCE_CODE = """result = a if a and b else c"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
