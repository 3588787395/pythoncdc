import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR18TernaryStarredCallWithPosArg(ExhaustiveTestCase):
    """Bug R18-11: f(*(a if c else b), other) — starred ternary + 位置参数。

    原始:
        f(*(a if c else b), other)
    缺陷: 函数调用中 *-starred 参数是 ternary，同时还有一个普通位置参数 other。
         R8 starred_call 测过 `f(*(ternary))` (仅 starred)，
         R17 starred_kwarg_call 测过 `f(*(ternary), key=val)` (starred + kwarg)。
         本用例 starred + 位置参数：CALL_FUNCTION_EX 的 LIST_EXTEND (消费 starred
         ternary) 与 LIST_APPEND (消费 other) 协调，ternary merge 块的
         LIST_EXTEND 之后还需 LIST_APPEND + LIST_TO_TUPLE。反编译完全丢失
         ternary 与 other 参数，退化为 `f()`，字节码指令数不匹配 (15 vs 9)。
    """
    SOURCE_CODE = """f(*(a if c else b), other)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
