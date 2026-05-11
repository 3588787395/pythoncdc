import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN16Try_While_If_Break_n_ValueError(ExhaustiveTestCase):
    SOURCE_CODE = """def f(values, limit):
    try:
        idx = 0
        while idx < len(values):
            if values[idx] > limit:
                break
            n = values[idx]
            idx += 1
    except ValueError:
        n = -1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
