import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN07Try_For_Break_n_StopIteration(ExhaustiveTestCase):
    SOURCE_CODE = """def f(values):
    try:
        for v in values:
            if v is None:
                break
            n = v
    except StopIteration:
        values = []"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
