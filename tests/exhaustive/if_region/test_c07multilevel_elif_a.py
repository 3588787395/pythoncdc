import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestC07Multilevel_Elif_a(ExhaustiveTestCase):
    SOURCE_CODE = """def f(a):
    if a > 100:
        a = 100
    elif a > 50:
        a = 50
    elif a > 20:
        a = 20
    elif a > 10:
        a = 10
    elif a > 0:
        a = 0
    else:
        a = -1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
