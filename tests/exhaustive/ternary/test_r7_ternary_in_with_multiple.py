import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInWithMultiple(ExhaustiveTestCase):
    """Bug R7: 多上下文管理器 with body 中 ternary 赋值 — 字节码不一致。

    原始:
        with ctx1, ctx2:
            y = a if c else b
    缺陷: 多上下文管理器 with 语句 body 中包含 ternary 赋值。多个
         BEFORE_WITH + WITH_EXIT 配对产生的嵌套 cleanup 路径与
         ternary merge 块的归属关系比单 with 更复杂。期望 ternary
         正确归约；当前疑似多 with 的 cleanup 链与 ternary entry 共享。
    """
    SOURCE_CODE = """with ctx1, ctx2:
    y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
