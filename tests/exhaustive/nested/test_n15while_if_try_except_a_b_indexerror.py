import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN15While_If_Try_Except_a_b_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """def f(data, limit):
    i = 0
    while i < len(data) and i < limit:
        if data[i] is not None:
            try:
                a = data[i][0]
            except IndexError:
                a = None
        i += 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
