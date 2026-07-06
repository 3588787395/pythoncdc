import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN06While_For_Break_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """def f(matrix, search):
    idx = 0
    while idx < len(matrix):
        for elem in matrix[idx]:
            if elem == search:
                break
        n = matrix[idx]
        idx += 1"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
