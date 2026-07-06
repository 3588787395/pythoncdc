import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN18With_For_If_Break_a_b(ExhaustiveTestCase):
    SOURCE_CODE = """def f(filename):
    with open(filename) as f:
        lines = f.readlines()
        for line in lines:
            if line.strip() == '':
                break
            a = line"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
