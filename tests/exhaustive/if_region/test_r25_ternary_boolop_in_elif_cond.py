import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25TernaryBoolopInElifCond(ExhaustiveTestCase):
    SOURCE_CODE = """def f(a, c, d, b):
    if a > 0:
        return 1
    elif (a if c else d) and b:
        return 2
    else:
        return 3"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
