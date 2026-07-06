import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestWL27WhileElseReturn_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    x = 5
    while x > 0:
        x = x - 1
    else:
        return x"""
    REGION_TYPE = "WHILE_LOOP"

    def test_decompile(self):
        self.verify_decompilation()
