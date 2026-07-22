import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernaryFuncDefDefault(ExhaustiveTestCase):
    """Bug R16 (new): def f(x=(a if c else b)): pass — func def ternary default arg。

    原始:
        def f(x=(a if c else b)):
            pass
    缺陷: 函数定义的默认参数值是 ternary。cond_block preload 含 LOAD_CONST
         f code + LOAD_CONST None + MAKE_FUNCTION + STORE_NAME f。MAKE_FUNCTION
         中 default tuple 包含 ternary 结果。R10 lambda_nested_default 已测过
         lambda default + ternary，R16 测 func def (非 lambda) + ternary default。
    """
    SOURCE_CODE = """def f(x=(a if c else b)):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
