import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN25TernaryNone_n(ExhaustiveTestCase):
    SOURCE_CODE = """n if n else None"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
