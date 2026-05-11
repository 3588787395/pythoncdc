import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN18With_For_If_Break_n_m(ExhaustiveTestCase):
    SOURCE_CODE = """def f(filepath):
    with open(filepath) as file:
        data = file.readlines()
        for row in data:
            if row.startswith('#'):
                break
            n = row"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
