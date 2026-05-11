import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL12WhileBreakElse_a(ExhaustiveTestCase):
    SOURCE_CODE = """while a > 0:
    a -= 1
    if a == 3:
        break
else:
    a = -1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
