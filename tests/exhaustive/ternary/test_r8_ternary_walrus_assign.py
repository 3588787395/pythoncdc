import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryWalrusAssign(ExhaustiveTestCase):
    """Bug R8: walrus 捕获 ternary 结果 — 字节码不一致。

    原始:
        (n := (a if c else b))
    缺陷: walrus 表达式捕获 ternary 结果。R1 测过 walrus 在
         ternary body/orelse 内 (`a if (n := x) else b`)。R8 测
         walrus 包裹整个 ternary：COPY+STORE n 在 merge_block 后
         续消费 ternary 结果，可能暴露 walrus 重建与 ternary
         value_target 推断的冲突。
    """
    SOURCE_CODE = """(n := (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
