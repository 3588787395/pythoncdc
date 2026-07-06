import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestC07Multilevel_Elif_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    if x < -100:
        x = -100
    elif x < -50:
        x = -50
    elif x < -20:
        x = -20
    elif x < -10:
        x = -10
    elif x < 0:
        x = 0
    else:
        x = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
