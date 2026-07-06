import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN12For_For_If_Break_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """def f(data, search):
    for idx, line in enumerate(data):
        for pos, elem in enumerate(line):
            if elem == search:
                break
        n = (idx, line)"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
