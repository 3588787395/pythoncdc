import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN25TernaryNone_a(ExhaustiveTestCase):
    SOURCE_CODE = """a if a else None"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
