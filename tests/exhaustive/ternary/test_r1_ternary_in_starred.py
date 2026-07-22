import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1TernaryInStarred(ExhaustiveTestCase):
    """Bug 9: ternary 在 starred 表达式中 — 丢失 star 展开。

    原始: x = [*(items if cond else [])]
    错误反编译:
        x = (items if cond else [])
    缺陷: 原始是 BUILD_LIST; <ternary>; BUILD_LIST; LIST_EXTEND; STORE x，
         即把 ternary 结果作为可迭代对象展开到列表字面量中。
         反编译器丢失了外层 [] 包装与 * 展开，直接赋值 ternary 结果。
         IfExp 在 AST 中存在，但字节码指令序列与原始不一致
         （缺 BUILD_LIST/LIST_EXTEND）。
    """
    SOURCE_CODE = """x = [*(items if cond else [])]"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
