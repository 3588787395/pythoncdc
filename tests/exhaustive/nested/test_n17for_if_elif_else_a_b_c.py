import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN17For_If_Elif_Else_a_b_c(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items):
    for item in items:
        if item > 0:
            a = item * 2
        elif item < 0:
            b = abs(item)
        else:
            c = 0"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
