import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernaryMultiFuncdefDefault(ExhaustiveTestCase):
    """Bug R17 (new): def f(x=ternary, y=ternary) — 多 ternary 作为函数默认参数。

    原始:
        def f(x=(a if c else b), y=(d if e else g)):
            return x + y
    缺陷: 多个 ternary 作为函数默认参数时，两个 ternary 的 merge 链式共享
         同一 BUILD_TUPLE 2 + MAKE_FUNCTION 出口。原反编译器误把 BUILD_TUPLE
         识别为元组字面量，整个函数定义退化为 `f = (ternary1, ternary2)`。
         依「父引用子入口」: 父 FunctionDef 通过 MAKE_FUNCTION 引用 chained
         ternary 子节点列表作为 defaults。
    """
    SOURCE_CODE = """def f(x=(a if c else b), y=(d if e else g)):
    return x + y
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
