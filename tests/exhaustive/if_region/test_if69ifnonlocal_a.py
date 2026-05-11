import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestIF69Ifnonlocal_a(ExhaustiveTestCase):
    SOURCE_CODE = """def f():
    a = 1
    def g():
        nonlocal a
        if a > 0:
            a = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
