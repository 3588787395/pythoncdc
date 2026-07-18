import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11TernaryReturnAnn(ExhaustiveTestCase):
    # if 体内函数返回类型注解为三元表达式
    SOURCE_CODE = """if c:
    def f() -> (a if c2 else b):
        return 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
