import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInCompareIn(ExhaustiveTestCase):
    """Bug R5-17: ternary 在 in 比较右端 — 字节码不一致。

    原始: r = x in (a if c else b)
    缺陷: ternary 作为 in 比较的右操作数时，CONTAINS_OP 在 merge_block 中
         消费 ternary 结果。R2 已通过简单 contains 场景（test_r2_ternary_in_contains）。
         R5 用 x in (ternary) 形式（右操作数为 ternary）重测。
         期望：Compare(ops=[In], left=x, comparators=[IfExp]) 正确归约。
    """
    SOURCE_CODE = """r = x in (a if c else b)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
