import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF63Ifmultireturn_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f(x):
    if x > 0:
        return 1
    elif x == 0:
        return 0
    else:
        return -1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
