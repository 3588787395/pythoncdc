import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestC06Nested_If_Else_In_If_a(ExhaustiveTestCase):
    SOURCE_CODE = """def f(a, b):
    if a > 0:
        if b > 0:
            a = b
        else:
            b = a"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
