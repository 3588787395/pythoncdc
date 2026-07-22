import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1TernaryInCompare(ExhaustiveTestCase):
    """Bug 7: ternary 作为 compare 左操作数 — 字节码严重不一致，丢失外层赋值。

    原始: x = (a if a > 0 else 0) == b
    错误反编译:
        (a if a > 0 else 0)
    缺陷: 原始是 ternary 求值后立即与 b 进行 COMPARE_OP(==)，
         再 STORE_NAME x。反编译器只保留了 ternary 表达式语句，
         丢失 == b 比较与外层 x 赋值。IfExp 在 AST 中存在，
         但字节码指令序列与原始不一致。
    """
    SOURCE_CODE = """x = (a if a > 0 else 0) == b"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
