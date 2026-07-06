import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN03For_For_Break_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """def f(data, search_val):
    for line in data:
        for elem in line:
            if elem == search_val:
                break
        n = line"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
