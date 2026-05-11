import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN29IfElifInWhile_x_var2(ExhaustiveTestCase):
    SOURCE_CODE = """while x > 0:
    if x > 5:
        x -= 2
    elif x > 2:
        x -= 1
    else:
        x = 0"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
