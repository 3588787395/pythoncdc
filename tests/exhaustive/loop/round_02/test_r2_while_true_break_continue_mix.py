import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2WhileTrueBreakContinueMix(ExhaustiveTestCase):
    SOURCE_CODE = """while True:
    if a:
        continue
    if b:
        break
    x = 1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
