import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestC06Nested_If_Else_In_If_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x, y):
    if x < 0:
        if y < 0:
            x = y
        else:
            y = x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
