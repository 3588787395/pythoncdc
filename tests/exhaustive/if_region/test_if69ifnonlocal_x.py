import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF69Ifnonlocal_x(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    x = 1
    def g():
        nonlocal x
        if x > 0:
            x = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
