import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL20WhileBreakContinue_a(ExhaustiveTestCase):
    SOURCE_CODE = """while a > 0:
    a -= 1
    if a == 5:
        continue
    if a == 2:
        break"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
