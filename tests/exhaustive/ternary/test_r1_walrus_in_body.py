import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1WalrusInBody(ExhaustiveTestCase):
    """Bug 1: walrus 在 ternary body 中 — 整体三元退化为 if-else-return，丢失 IfExp 与赋值目标 x。

    原始: x = (y := a) if a > 0 else 0
    错误反编译:
        if (a > 0):
            y = a
        else:
            return 0
    缺陷: 既丢失了外层赋值目标 x，又把模块级语句错造为 return 语句，
         未识别为 TERNARY 区域，IfExp AST 节点缺失。
    """
    SOURCE_CODE = """x = (y := a) if a > 0 else 0"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
