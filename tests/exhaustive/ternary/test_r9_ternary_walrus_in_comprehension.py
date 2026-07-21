import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryWalrusInComprehension(ExhaustiveTestCase):
    """Bug R9: comprehension 内 walrus(ternary) — 字节码不一致。

    原始:
        x = [(n := (a if c else b)) for i in r]
    缺陷: list comprehension 内 walrus 捕获 ternary 结果。R8 已测过
         walrus + ternary。R9 测 comprehension 内 walrus(ternary) 变体：
         ternary merge 块作为 walrus 的 COPY + STORE 源，与 LIST_APPEND
         的栈顺序、walrus 副作用在 comprehension 闭包内的捕获可能冲突。
    """
    SOURCE_CODE = """x = [(n := (a if c else b)) for i in r]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
