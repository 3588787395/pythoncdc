import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1WalrusInOrelse(ExhaustiveTestCase):
    """Bug 2: walrus 在 ternary orelse 中 — 三元整体退化为 if-else，丢失 IfExp 与外层赋值。

    原始: x = a if cond else (y := b)
    错误反编译:
        if cond:
            return a
        else:
            y = b
    缺陷: 整体三元表达式未被识别为 TERNARY 区域，
         orelse 分支被识别为赋值语句后丢失外层 x 绑定；
         true 分支错造为模块级 return。
    """
    SOURCE_CODE = """x = a if cond else (y := b)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
