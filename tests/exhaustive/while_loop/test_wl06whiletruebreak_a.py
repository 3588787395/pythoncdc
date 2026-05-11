import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL06WhileTrueBreak_a(ExhaustiveTestCase):
    SOURCE_CODE = """while True:
    a += 1
    if a > 100:
        break"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
