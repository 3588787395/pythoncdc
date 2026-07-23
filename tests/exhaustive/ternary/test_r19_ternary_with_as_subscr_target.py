import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryWithAsSubscriptTarget(ExhaustiveTestCase):
    """Bug R19-02: with ctx() as cm[(ternary)] — ternary 作 with as-target 的 subscript 下标。

    原始:
        with ctx() as cm[(a if c else b)]:
            pass
    缺陷: with 语句的 as-target 是 subscript 形式 cm[(ternary)] —— ternary 是
         下标。R3 with_as 测过 `with ctx() as (ternary)` (ternary 直接作 as-target
         Name)，R18 for_iter_subscr 测过 `for x in y[(ternary)]` (for iter subscript)。
         本用例 ternary 是 with as-target 的 subscript：BEFORE_WITH + STORE_SUBSCR
         消费链与 ternary merge 块归属冲突，反编译退化为 `with ctx(): (ternary)`，
         丢失 as-target 与 subscript 结构。
    """
    SOURCE_CODE = """with ctx() as cm[(a if c else b)]:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
