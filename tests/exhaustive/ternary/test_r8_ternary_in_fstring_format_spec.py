import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryInFstringFormatSpec(ExhaustiveTestCase):
    """Bug R8: f-string format_spec 是 ternary — 字节码不一致。

    原始:
        x = f"{val:{a if c else b}}"
    缺陷: f-string 的 format_spec 部分是 ternary。FORMAT_VALUE
         flags 含 bit2 (has format_spec) 时，栈顶之下是 format_spec。
         R8 测 format_spec 是 ternary 变体：ternary merge 块的栈
         输出作为 format_spec，与 FORMAT_VALUE + BUILD_STRING 的
         栈顺序可能冲突。
    """
    SOURCE_CODE = """x = f"{val:{a if c else b}}"
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
