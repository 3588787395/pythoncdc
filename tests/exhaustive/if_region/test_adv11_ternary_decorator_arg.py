import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11TernaryDecoratorArg(ExhaustiveTestCase):
    # if 体内装饰器参数为三元表达式
    SOURCE_CODE = """if c:
    @dec(a if c2 else b)
    def f():
        return 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
