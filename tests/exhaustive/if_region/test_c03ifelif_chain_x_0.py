import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestC03IfElif_Chain_x_0(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    if x < -10:
        x = -10
    elif x < -5:
        x = -5
    elif x < 0:
        x = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
