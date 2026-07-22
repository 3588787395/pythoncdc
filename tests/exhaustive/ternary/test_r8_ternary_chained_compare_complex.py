import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryChainedCompareComplex(ExhaustiveTestCase):
    """Bug R8: chained compare 中间操作数是 ternary — 字节码不一致。

    原始:
        x = 0 < (a if c else b) < 10
    缺陷: 链式比较的中间操作数是 ternary。R5 已测过 chained compare
         与 ternary 的组合。R8 测中间操作数变体：ternary merge 块
         作为链式比较的中间值，需要 COPY 模板与 COMPARE_OP 的栈顺序
         配合，可能与 ternary value_target 推断冲突。
    """
    SOURCE_CODE = """x = 0 < (a if c else b) < 10
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
