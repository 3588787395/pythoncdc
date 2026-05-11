import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN23TernaryStr_n(ExhaustiveTestCase):
    SOURCE_CODE = """'yes' if n else 'no'"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
