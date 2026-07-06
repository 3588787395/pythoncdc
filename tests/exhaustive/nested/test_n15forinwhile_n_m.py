import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN15ForInWhile_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """while n > 0:
    for m in range(n):
        pass
    n -= 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
