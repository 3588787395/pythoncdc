import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL32WhileMultiBreak_n(ExhaustiveTestCase):
    SOURCE_CODE = """n = 0
while n < 100:
    if n == 3:
        break
    if n == 7:
        break
    n += 1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
