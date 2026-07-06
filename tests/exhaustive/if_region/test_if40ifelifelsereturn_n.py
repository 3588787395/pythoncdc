import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF40Ifelifelsereturn_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(n):
    if n > 0:
        return 1
    elif n < 0:
        return -1
    else:
        return 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
