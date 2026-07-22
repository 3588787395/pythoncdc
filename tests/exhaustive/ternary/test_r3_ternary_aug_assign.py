import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryAugAssign(ExhaustiveTestCase):
    """Bug R3-17: ternary 在 augmented assign 右值 — 字节码不一致。

    原始: x += (a if cond else b)
    缺陷: ternary 在 augmented assign 右值时，LOAD_NAME + BINARY_OP + STORE_NAME
         在 merge_block 中消费 ternary 结果。反编译器可能丢失 += 结构。
    """
    SOURCE_CODE = """x += (a if cond else b)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
