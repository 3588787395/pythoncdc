import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1ChainedCompareInCond(ExhaustiveTestCase):
    """Bug 5: ternary 条件为 chained compare — 整体三元退化为 if-else-return。

    原始: x = a if 0 < a < 10 else 0
    错误反编译:
        if (0 < a < 10):
            return a
        else:
            return 0
    缺陷: 条件为链式比较 `0 < a < 10` 时，反编译器未识别 TERNARY 区域，
         整体退化为 if-else 语句，且模块级语句错造为 return 语句，
         失去外层 x 赋值绑定。IfExp AST 节点缺失，字节码严重不一致。
    """
    SOURCE_CODE = """x = a if 0 < a < 10 else 0"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
