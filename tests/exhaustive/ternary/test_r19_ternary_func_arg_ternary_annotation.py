import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryFuncArgTernaryAnnotation(ExhaustiveTestCase):
    """Bug R19-09: def f(x: (A if c else B)) — ternary 作函数参数注解。

    原始:
        def f(x: (A if c else B)):
            pass
    缺陷: 函数参数 x 的注解是 ternary。R8 annotation_default 测过
         `x: int = (ternary)` (注解常量 + 默认值 ternary)。本用例注解本身是
         ternary：MAKE_FUNCTION 时 BUILD_TUPLE 收集注解，注解 ternary 的
         merge 块在 MAKE_FUNCTION 之前汇聚。ternary merge 块归属与函数定义
         的 MAKE_FUNCTION 消费链冲突，反编译退化为 `def f(x): return None`，
         完全丢失注解 ternary (IfExp MISSING)，字节码指令数不匹配 (11 vs 6)。
    """
    SOURCE_CODE = """def f(x: (A if c else B)):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
