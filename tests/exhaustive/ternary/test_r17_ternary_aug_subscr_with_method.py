import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernaryAugSubscrWithMethod(ExhaustiveTestCase):
    """Bug R17-12: x[(a if c else b).method()] += 1 — aug assign subscr with ternary.method() index。

    原始:
        x[(a if c else b).method()] += 1
    缺陷: augmented subscript assignment 的索引是 (ternary).method()。
         ternary merge 块栈顶经 LOAD_METHOD method + PRECALL + CALL 后作为
         BINARY_SUBSCR 索引，再 LOAD + BINARY_OP + STORE_SUBSCR。R12
         aug_assign_subscr 测过 x[a if c else b] += 1 (ternary 直接作索引)，
         R16 subscr_aug_assign 测过类似，但 (ternary).method() 作索引未覆盖。
         反编译退化为 (a if c else b).method()，丢失 x[...] += 1，
         指令数严重不匹配 (18 vs 10)。
    """
    SOURCE_CODE = """x[(a if c else b).method()] += 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
