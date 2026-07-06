import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL32WhileMultiBreak_x(ExhaustiveTestCase):
    SOURCE_CODE = """x = 0
while x < 100:
    if x < 10:
        break
    if x > 90:
        break
    x += 1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
