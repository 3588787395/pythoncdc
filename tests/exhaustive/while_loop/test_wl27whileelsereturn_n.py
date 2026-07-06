import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL27WhileElseReturn_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    n = 10
    while n > 0:
        n -= 1
    else:
        return -1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
