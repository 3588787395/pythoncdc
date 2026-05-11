import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestC03IfElif_Chain_n_42(ExhaustiveTestCase):
    SOURCE_CODE = """def f(n):
    if n > 100:
        n = 100
    elif n > 50:
        n = 50
    elif n > 0:
        n = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
