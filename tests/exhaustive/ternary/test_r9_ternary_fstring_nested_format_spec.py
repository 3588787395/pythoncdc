import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryFstringNestedFormatSpec(ExhaustiveTestCase):
    """Bug R9: f-string 嵌套 format_spec 含 ternary — 字节码不一致。

    原始:
        x = f"{val:{(a if c else b)}}"
    缺陷: f-string 的 format_spec 部分是嵌套的 ternary（带额外括号）。
         R8 已测过 f-string format_spec ternary。R9 测嵌套变体：
         FORMAT_VALUE + BUILD_STRING 的栈顺序与 ternary merge 块的
         嵌套括号重建可能冲突。
    """
    SOURCE_CODE = """x = f"{val:{(a if c else b)}}"
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
