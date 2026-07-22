import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInContains(ExhaustiveTestCase):
    """Bug R2-39: ternary 在 in/not in 测试中 — 字节码不一致。

    原始: x = (a if cond else b) in collection
    缺陷: ternary 在 in 测试中时，CONTAINS_OP 在 merge_block 中消费 ternary 结果
         与 collection。反编译器可能丢失 in collection 测试。
    """
    SOURCE_CODE = """x = (a if cond else b) in collection"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
