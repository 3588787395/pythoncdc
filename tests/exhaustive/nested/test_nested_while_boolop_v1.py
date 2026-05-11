import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestNestedWhileBoolop_v1(ExhaustiveTestCase):
    SOURCE_CODE = """while x:
    y = x and y and z"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
