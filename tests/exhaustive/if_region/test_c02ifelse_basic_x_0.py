import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestC02IfElse_Basic_x_0(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    if x < 0:
        x = 0
    else:
        x = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
