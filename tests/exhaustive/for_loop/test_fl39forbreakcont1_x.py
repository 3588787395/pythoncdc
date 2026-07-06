import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL39ForBreakCont1_x(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(50):
    if x < 5:
        continue
    if x > 40:
        break
    y = x"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
