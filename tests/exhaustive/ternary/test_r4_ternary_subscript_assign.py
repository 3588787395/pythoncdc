import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernarySubscriptAssign(ExhaustiveTestCase):
    """Bug R4-10: ternary 作为 subscript 赋值目标索引 — 字节码不一致。

    原始: x[a if cond else b] = 1
    缺陷: ternary 作为 subscript store 的索引时，STORE_SUBSCR 在 merge_block
         中消费 ternary 结果与 value。反编译器可能丢失 STORE_SUBSCR 结构或
         ternary 结构。
    """
    SOURCE_CODE = """x[a if cond else b] = 1"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
