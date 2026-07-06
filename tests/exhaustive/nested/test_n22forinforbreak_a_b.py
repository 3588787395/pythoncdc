import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN22ForInForBreak_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """for a in range(3):
    for b in range(3):
        if b == 1:
            break"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
