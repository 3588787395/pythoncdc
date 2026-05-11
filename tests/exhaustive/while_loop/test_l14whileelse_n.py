import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestL14WhileElse_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(n):
    i = 0
    while i < n:
        n = i
        i += 1
    else:
        n = -1"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
