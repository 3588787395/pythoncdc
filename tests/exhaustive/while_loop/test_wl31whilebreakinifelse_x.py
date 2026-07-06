import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL31WhileBreakInIfElse_x(ExhaustiveTestCase):
    SOURCE_CODE = """x = 0
while x < 20:
    if x % 2 == 0:
        x = x + 1
    else:
        break"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
