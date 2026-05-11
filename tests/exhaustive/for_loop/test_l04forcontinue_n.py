import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL04ForContinue_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items):
    for item in items:
        if item <= 0:
            continue
        n = item"""
    REGION_TYPE = "FOR_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
