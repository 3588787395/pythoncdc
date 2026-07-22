import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryDeep5Level(ExhaustiveTestCase):
    """Bug R9: 5 层嵌套 ternary 边界 — 字节码不一致。

    原始:
        x = a1 if c1 else (a2 if c2 else (a3 if c3 else (a4 if c4 else (a5 if c5 else b5))))
    缺陷: 5 层嵌套 ternary。内层 ternary merge 块作为外层 ternary 的
         false_value，5 层嵌套导致 condition/true/false/merge 块数量
         增多，自底向上归约顺序可能因块归属冲突而失败。
    """
    SOURCE_CODE = """x = a1 if c1 else (a2 if c2 else (a3 if c3 else (a4 if c4 else (a5 if c5 else b5))))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
