import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInCompareRight(ExhaustiveTestCase):
    """Bug R2-25: ternary 作为 compare 右操作数 — 字节码不一致。

    原始: x = b == (a if cond else 0)
    缺陷: ternary 作为 compare 右操作数时，左操作数 b 在 ternary entry 之前被加载
         并"困"在栈上，merge_block 的 COMPARE_OP 消费 b 和 ternary 结果。
         反编译器可能丢失 b == 比较与外层 x 赋值。
    """
    SOURCE_CODE = """x = b == (a if cond else 0)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
