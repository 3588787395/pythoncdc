import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1TernaryInSlice(ExhaustiveTestCase):
    """Bug 6: ternary 在切片下标中 — 字节码严重不一致，丢失外层赋值。

    原始: x = lst[a if cond else 0:b if cond2 else -1]
    错误反编译:
        (a if cond else 0)
        x = (b if cond2 else -1)
    缺陷: 原始是 BUILD_SLICE 2 + BINARY_SUBSCR 的复合表达式，
         反编译器把切片拆解为两个独立表达式语句，丢失 lst 引用
         与 BUILD_SLICE/BINARY_SUBSCR 结构。IfExp 在 AST 中存在，
         但字节码指令序列与原始严重不一致。
    """
    SOURCE_CODE = """x = lst[a if cond else 0:b if cond2 else -1]"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
