import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFL38ForMultiContinue_x(ExhaustiveTestCase):
    SOURCE_CODE = """for x in range(100):
    if x % 2 == 0:
        continue
    if x % 3 == 0:
        continue
    y = x"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
