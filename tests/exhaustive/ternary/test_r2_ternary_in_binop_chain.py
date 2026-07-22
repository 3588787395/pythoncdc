import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInBinopChain(ExhaustiveTestCase):
    """Bug R2-19: ternary 在 binary operation 链中间 — 字节码不一致。

    原始: x = a + (b if cond else 0) + c
    缺陷: ternary 作为 BinOp 链中间元素时，左操作数 a 在 ternary entry 之前
         被加载并"困"在栈上，右操作数 c 在 ternary merge 之后。
         反编译器可能丢失 +c 操作或 +a 操作。
    """
    SOURCE_CODE = """x = a + (b if cond else 0) + c"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
