import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN05While_If_Continue_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(val, max_val):
    while val < max_val:
        if val < 10:
            continue
        n = val ** 2
        val += 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
