import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInWithBody(ExhaustiveTestCase):
    """Bug R7: with body 中 ternary 赋值 — 字节码不一致。

    原始:
        with ctx:
            y = a if c else b
    缺陷: with 语句 body 中包含 ternary 赋值。R1 已测 with (ternary) as f
         (ternary 在上下文管理器位置，test_r1_ternary_in_with)。R7 测
         ternary 在 with body 内的位置：BEFORE_WITH + WITH_EXIT 之间
         的 body 块包含 ternary merge，可能与 with 的 cleanup 路径交互。
    """
    SOURCE_CODE = """with ctx:
    y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
