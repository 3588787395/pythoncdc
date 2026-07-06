import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN29IfElifInWhile_a_var2(ExhaustiveTestCase):
    SOURCE_CODE = """while a > 0:
    if a > 5:
        a -= 2
    elif a > 2:
        a -= 1
    else:
        a = 0"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
