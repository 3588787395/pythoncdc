import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestC03IfElif_Chain_a_3(ExhaustiveTestCase):
    SOURCE_CODE = """def f(a):
    if a > 10:
        a = 10
    elif a > 5:
        a = 5
    elif a > 0:
        a = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
