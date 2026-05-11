import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL20WhileBreakContinue_x(ExhaustiveTestCase):
    SOURCE_CODE = """while x > 0:
    x -= 1
    if x == 5:
        continue
    if x == 2:
        break"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
