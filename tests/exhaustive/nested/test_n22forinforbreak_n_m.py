import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN22ForInForBreak_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """for n in range(3):
    for m in range(3):
        if m == 1:
            break"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
