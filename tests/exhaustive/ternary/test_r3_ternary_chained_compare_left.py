import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryChainedCompareLeft(ExhaustiveTestCase):
    """Bug R3-01: ternary 在 chained compare 左端 — 字节码不一致。

    原始: x = (a if cond else 1) < 10 < 100
    缺陷: ternary 在 chained compare 左端时，COPY 2 复制 ternary 结果供后续
         比较段使用。反编译器可能丢失 chained compare 结构。
    """
    SOURCE_CODE = """x = (a if cond else 1) < 10 < 100"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
