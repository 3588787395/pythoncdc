import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL49ForElseBreakAssign_n(ExhaustiveTestCase):
    SOURCE_CODE = """for n in range(10):
    if n == 5:
        break
    x = n
else:
    x = -1"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
