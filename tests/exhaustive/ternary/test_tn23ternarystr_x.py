import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN23TernaryStr_x(ExhaustiveTestCase):
    SOURCE_CODE = """'yes' if x else 'no'"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
