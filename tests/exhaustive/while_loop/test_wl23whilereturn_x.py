import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL23WhileReturn_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    while x > 0:
        x -= 1
        if x == 0:
            return x"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
