import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN29IfElifInWhile_n_var2(ExhaustiveTestCase):
    SOURCE_CODE = """while n > 0:
    if n > 5:
        n -= 2
    elif n > 2:
        n -= 1
    else:
        n = 0"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
