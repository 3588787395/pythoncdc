import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL23WhileReturn_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(n):
    while n > 0:
        n -= 1
        if n == 0:
            return n"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
