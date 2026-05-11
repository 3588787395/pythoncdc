import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN12For_For_If_Break_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """def f(matrix, target):
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            if val == target:
                break
        a = (i, row)"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
