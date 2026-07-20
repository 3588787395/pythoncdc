import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv09NestedFuncDefaultWalrus(ExhaustiveTestCase):
    # if 体内嵌套函数默认值 walrus def f(x=(n := 1)): return x
    SOURCE_CODE = """if c:
    def f(x=(n := 1)):
        return x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
