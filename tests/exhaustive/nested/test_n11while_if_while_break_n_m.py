import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN11While_If_While_Break_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """def f(val, max_val):
    while val < max_val:
        if val > 0:
            cnt = 0
            while cnt < 20:
                if cnt == 10:
                    break
                cnt += 1
        n = val
        val += 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
