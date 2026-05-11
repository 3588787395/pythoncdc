import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN08For_Try_Except_n_ValueError(ExhaustiveTestCase):
    SOURCE_CODE = """def f(strings):
    for s in strings:
        try:
            n = int(s)
        except ValueError:
            n = -1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
