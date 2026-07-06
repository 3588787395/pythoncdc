import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN10For_If_For_Break_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """def f(data, search):
    for line in data:
        if line is not None:
            for elem in line:
                if elem == search:
                    break
            n = line"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
