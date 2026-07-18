import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11TernaryKwonlyDefault(ExhaustiveTestCase):
    # if 体内函数 kw-only 参数默认值为三元表达式
    SOURCE_CODE = """if c:
    def f(*, x=a if c2 else b):
        return x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
