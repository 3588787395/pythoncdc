import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL16WhileBreak_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items):
    i = 0
    while i < len(items):
        if items[i] < 0:
            break
        x = items[i]
        i += 1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
