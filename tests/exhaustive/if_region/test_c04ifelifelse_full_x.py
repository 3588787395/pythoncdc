import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestC04IfElifElse_Full_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    if x < -10:
        x = -10
    elif x < -5:
        x = -5
    else:
        x = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
