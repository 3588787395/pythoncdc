import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN32TryInForBreak_n_StopIteration(ExhaustiveTestCase):
    SOURCE_CODE = """for n in range(10):
    try:
        if n == 5:
            break
    except StopIteration:
        continue"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
