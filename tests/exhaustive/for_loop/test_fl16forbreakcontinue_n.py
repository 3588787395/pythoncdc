import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL16ForBreakContinue_n(ExhaustiveTestCase):
    SOURCE_CODE = """for n in range(20):
    if n == 3:
        continue
    if n == 7:
        break"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
