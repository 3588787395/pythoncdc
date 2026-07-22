import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInCompareIs(ExhaustiveTestCase):
    """Bug R5-16: ternary 在 is 比较右端 — 字节码不一致。

    原始: r = x is (a if c else b)
    缺陷: ternary 作为 is 比较的右操作数时，IS_OP 在 merge_block 中消费
         ternary 结果。R2 已通过 is None 场景（test_r2_ternary_in_is_none）。
         R5 用 is (ternary) 形式（右操作数为 ternary）重测。
         期望：Compare(ops=[Is], left=x, comparators=[IfExp]) 正确归约。
    """
    SOURCE_CODE = """r = x is (a if c else b)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
