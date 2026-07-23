import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryBoolopOrTwoAssign(ExhaustiveTestCase):
    """Bug R20-10: x = (a if c else b) or (d if e else f) — 赋值 RHS 是两 ternary 的 boolop OR。

    原始:
        x = (a if c else b) or (d if e else f)
    缺陷: 赋值 RHS 是两个 ternary 通过 `or` 短路组合。R14 assert_two_ternaries_boolop
         测过 assert (ternary) and (ternary) (AND 变体)。本用例是 OR 变体 +
         赋值上下文：JUMP_IF_TRUE_OR_POP 短路 + 第二个 ternary merge + STORE_NAME x。
         反编译把两个 ternary 拆成独立语句 `x = (d if e else f)` + `(a if c else b)`，
         丢失 JUMP_IF_TRUE_OR_POP 短路与 or 结构，指令数不匹配 (11 vs 14)。
    """
    SOURCE_CODE = """x = (a if c else b) or (d if e else f)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
