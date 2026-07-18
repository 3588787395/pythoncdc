import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09GlobalMulti(ExhaustiveTestCase):
    # if 体内 global 多名声明 global a, b, c
    SOURCE_CODE = """def f():
    if cond:
        global a, b, c
        a = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
