import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN25TernaryNone_x(ExhaustiveTestCase):
    SOURCE_CODE = """x if x else None"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
