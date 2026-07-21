import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryDeep10Level(ExhaustiveTestCase):
    """Bug R9: 10 层嵌套 ternary 边界 — 字节码不一致。

    原始:
        x = (10 层嵌套 ternary)
    缺陷: 10 层嵌套 ternary 边界测试。深度递归的 ternary 链可能暴露
         自底向上归约栈深度限制、块归属推断的递归边界。
    """
    SOURCE_CODE = """x = a1 if c1 else (a2 if c2 else (a3 if c3 else (a4 if c4 else (a5 if c5 else (a6 if c6 else (a7 if c7 else (a8 if c8 else (a9 if c9 else (a10 if c10 else b10)))))))))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
