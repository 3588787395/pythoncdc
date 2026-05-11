import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL30WhileBreakInTry_x(ExhaustiveTestCase):
    SOURCE_CODE = """x = 0
while x < 20:
    try:
        y = 10 // x
        if y == 0:
            break
    except ZeroDivisionError:
        break
    x += 1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
