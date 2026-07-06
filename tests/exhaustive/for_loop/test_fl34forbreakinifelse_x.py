import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL34ForBreakInIfElse_x(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(20):
    if x % 2 == 0:
        x = x + 1
    else:
        break"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
