import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL20WhileBreakContinue_n(ExhaustiveTestCase):
    SOURCE_CODE = """while n > 0:
    n -= 1
    if n == 5:
        continue
    if n == 2:
        break"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
