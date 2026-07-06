import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestC07Multilevel_Elif_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(n):
    if n > 1000:
        n = 1000
    elif n > 500:
        n = 500
    elif n > 200:
        n = 200
    elif n > 100:
        n = 100
    elif n > 50:
        n = 50
    else:
        n = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
