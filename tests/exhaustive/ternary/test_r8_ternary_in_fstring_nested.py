import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryInFstringNested(ExhaustiveTestCase):
    """Bug R8: f-string 中嵌套 ternary + 字面量 — 字节码不一致。

    原始:
        x = f"prefix-{a if c else b}-suffix"
    缺陷: f-string 内嵌套 ternary 表达式，前后带字面量。
         R2 已测过 f-string 中 ternary。R8 测带前后字面量变体：
         BUILD_STRING 3 在 merge_block 消费 ternary FORMAT_VALUE
         与 LOAD_CONST "prefix"/"suffix"，可能暴露 ternary chain
         与 BUILD_STRING 的栈顺序冲突。
    """
    SOURCE_CODE = """x = f"prefix-{a if c else b}-suffix"
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
