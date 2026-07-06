import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTN24TernaryBool_a(ExhaustiveTestCase):
    SOURCE_CODE = """True if a else False"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
