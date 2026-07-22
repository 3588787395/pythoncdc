import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInBinopLeft(ExhaustiveTestCase):
    """Bug R2-3: ternary 作为 binary operation 左操作数 — 字节码不一致。

    原始: x = (a if cond else 0) + b
    缺陷: ternary 作为 BinOp 左操作数时，ternary 求值后 LOAD b + BINARY_OP
         在 merge_block 中。反编译器可能丢失 + b 与外层赋值。
    """
    SOURCE_CODE = """x = (a if cond else 0) + b"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
