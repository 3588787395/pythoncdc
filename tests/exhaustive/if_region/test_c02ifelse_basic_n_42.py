import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestC02IfElse_Basic_n_42(ExhaustiveTestCase):
    SOURCE_CODE = """def f(n):
    if n > 42:
        n = 42
    else:
        n = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
