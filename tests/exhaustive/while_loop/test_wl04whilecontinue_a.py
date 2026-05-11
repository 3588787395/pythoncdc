import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL04WhileContinue_a(ExhaustiveTestCase):
    SOURCE_CODE = """while a > 0:
    a -= 1
    if a == 5:
        continue"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
