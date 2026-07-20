import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInChainedCompare(ExhaustiveTestCase):
    """Bug R2-33: ternary 在 chained compare 中间 — 字节码不一致。

    原始: x = 0 < (a if cond else 1) < 10
    缺陷: ternary 在 chained compare 中间时，COPY 2 复制 ternary 结果供后续
         比较段使用。merge_block 含 SWAP / COPY 2 / COMPARE_OP 序列。
         反编译器可能丢失 chained compare 结构。
    """
    SOURCE_CODE = """x = 0 < (a if cond else 1) < 10"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
