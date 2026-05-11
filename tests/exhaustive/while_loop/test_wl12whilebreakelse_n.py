import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL12WhileBreakElse_n(ExhaustiveTestCase):
    SOURCE_CODE = """while n > 0:
    n -= 1
    if n == 3:
        break
else:
    n = -1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
