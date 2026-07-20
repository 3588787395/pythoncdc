import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11TernaryFuncDefault(ExhaustiveTestCase):
    # if 体内函数位置参数默认值为三元表达式 def f(x=a if c2 else b):
    SOURCE_CODE = """if c:
    def f(x=a if c2 else b):
        return x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
