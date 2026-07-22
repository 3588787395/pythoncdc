import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInIsNone(ExhaustiveTestCase):
    """Bug R2-36: ternary 与 is None 测试组合 — 字节码不一致。

    原始: x = (a if cond else b) is None
    缺陷: ternary 在 is None 测试中时，IS_OP 在 merge_block 中消费 ternary 结果。
         反编译器可能丢失 is None 测试与外层赋值。
    """
    SOURCE_CODE = """x = (a if cond else b) is None"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
