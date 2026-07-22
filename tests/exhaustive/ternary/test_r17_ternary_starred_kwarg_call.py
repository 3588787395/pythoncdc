import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernaryStarredKwargCall(ExhaustiveTestCase):
    """Bug R17-04: f(*(a if c else b), key=val) — starred ternary + kwarg in call。

    原始:
        f(*(a if c else b), key=val)
    缺陷: 函数调用中 *-starred 参数是 ternary，同时还有 keyword 参数 key=val。
         CALL 指令的 KW_NAMES 与 ternary merge 块的 BUILD_LIST/UNPACK_EX
         消费链冲突。反编译器完全丢失 starred ternary 参数，退化为
         `f(key=val)`，字节码指令数不匹配 (13 vs 10)。
    """
    SOURCE_CODE = """f(*(a if c else b), key=val)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
