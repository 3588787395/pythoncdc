import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryOrelseChain(ExhaustiveTestCase):
    """Bug R2-17: 双层嵌套 ternary (orelse 链) — 字节码不一致。

    原始: x = a if c1 else (b if c2 else c)
    缺陷: 双层嵌套 ternary 在 orelse 中递归，需要 _build_simple_ternary_value
         正确识别内层 ternary。可能退化为多个独立表达式语句。
    """
    SOURCE_CODE = """x = a if c1 else (b if c2 else c)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
