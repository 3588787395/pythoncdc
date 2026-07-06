import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL33ForBreakInTry_x(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(20):
    try:
        y = 1 // x
        if y == 0:
            break
    except ZeroDivisionError:
        break"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
