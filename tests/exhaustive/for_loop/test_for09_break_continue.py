import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestFor09BreakContinue(ExhaustiveTestCase):
    SOURCE_CODE = """for i in range(20):
    if i < 5:
        continue
    if i > 10:
        break
    x = i"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
