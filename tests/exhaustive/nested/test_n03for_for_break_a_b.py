import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN03For_For_Break_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """def f(matrix, target):
    for row in matrix:
        for val in row:
            if val == target:
                break
        a = row"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
