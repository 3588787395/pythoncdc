import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN14If_For_Try_Except_a_b_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """def f(matrix, flag):
    if flag:
        for row in matrix:
            try:
                a = row[0]
            except IndexError:
                a = None"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
