import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInBinopRight(ExhaustiveTestCase):
    """Bug R2-2: ternary 作为 binary operation 右操作数 — 字节码不一致。

    原始: x = a + (b if cond else 0)
    缺陷: ternary 作为 BinOp 右操作数时，左操作数 a 在 ternary entry 之前
         被加载并"困"在栈上，merge_block 的 BINARY_OP 消费 a 和 ternary 结果。
         反编译器可能丢失外层 BinOp 结构或丢失 a 操作数。
    """
    SOURCE_CODE = """x = a + (b if cond else 0)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
