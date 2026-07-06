import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN01For_If_Break_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """def f(values, limit):
    for v in values:
        if v > limit:
            break
        n = v"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
