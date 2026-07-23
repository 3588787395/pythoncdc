import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryAssertMsgBinopTwo(ExhaustiveTestCase):
    """Bug R20-13: assert x, (a if c else b) + (d if e else f) — assert msg 是两 ternary 的 binop。

    原始:
        assert x, (a if c else b) + (d if e else f)
    缺陷: assert 的 message 是两个 ternary 的 BINARY_OP (+) 组合（无字符串前缀）。
         R8 assert_binop_msg 测过 assert x, "msg: " + (ternary) (字符串 + 单 ternary)。
         本用例 msg 是 ternary + ternary：第一个 ternary merge 块栈顶 + 第二个
         ternary merge 块栈顶 + BINARY_OP + LOAD_ASSERTION_ERROR + RAISE_VARARGS。
         反编译退化为 `assert x, e` + `raise (d if e else f)()`，把第二个 ternary
         误识为 raise 调用，丢失 BINARY_OP 与第一个 ternary，指令数不匹配 (15 vs 14)。
    """
    SOURCE_CODE = """assert x, (a if c else b) + (d if e else f)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
