import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInSubscript(ExhaustiveTestCase):
    """Bug R2-7: ternary 作为 subscript 索引 — 字节码不一致。

    原始: x = lst[a if cond else 0]
    缺陷: ternary 作为 BINARY_SUBSCR 的索引时，左操作数 lst 在 ternary entry
         之前被加载并"困"在栈上，merge_block 的 BINARY_SUBSCR 消费 lst 和 ternary 结果。
         反编译器可能丢失 lst[...] 的索引访问结构。
    """
    SOURCE_CODE = """x = lst[a if cond else 0]"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
