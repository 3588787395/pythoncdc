import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR18TernaryForIterSubscr(ExhaustiveTestCase):
    """Bug R18-09: for x in y[(a if c else b)]: pass — for iter 是 subscript 含 ternary。

    原始:
        for x in y[(a if c else b)]:
            pass
    缺陷: for 循环的 iter 表达式是 y[(ternary)] —— subscript 下标是 ternary。
         R2 for_iter 测过 `for x in (ternary)` (ternary 直接作 iter)，
         R14 for_iter_list_middle 测过 `for x in [1, (ternary), 2]`。
         本用例 ternary 是 subscript 的下标：ternary merge 块的 BINARY_SUBSCR
         之后才走 GET_ITER + FOR_ITER。反编译丢失 subscript 与 ternary，
         退化为 `for x in y:`，字节码指令数不匹配 (10 vs 8)。
    """
    SOURCE_CODE = """for x in y[(a if c else b)]:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
