import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTE02NestedTernary_x(ExhaustiveTestCase):
    SOURCE_CODE = '''result = x if x > y else (y if y > z else z)'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
