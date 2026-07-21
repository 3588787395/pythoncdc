import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryNestedWithBody(ExhaustiveTestCase):
    """Bug R8: 嵌套 with body 中 ternary 赋值 — 字节码不一致。

    原始:
        with outer:
            with inner:
                y = a if c else b
    缺陷: 嵌套 with 语句 body 中包含 ternary 赋值。R7 已测单 with
         body + ternary (test_r7_ternary_in_with_body) 通过，多 with
         (test_r7_ternary_in_with_multiple) 通过。R8 测嵌套 with 变体：
         内层 with 的 BEFORE_WITH + WITH_EXIT 在外层 with body 内，
         两层 cleanup 链与 ternary merge 块的归属可能冲突。
    """
    SOURCE_CODE = """with outer:
    with inner:
        y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
