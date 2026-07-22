import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInAssertMsg(ExhaustiveTestCase):
    """Bug R7: assert 的 message 是 ternary — 字节码不一致。

    原始:
        assert x, (a if c else b)
    缺陷: assert 的 message 位置使用 ternary。R1 已测 assert_simple
         (ternary 在 message 位置？实际是简单 assert)，R4 已测
         ternary 在 test 位置 (test_r4_ternary_in_assert)。R7 测
         ternary 在 message 位置：测试表达式是简单变量，message 是
         ternary。当测试为真时 ternary 不应求值，但当测试为假时
         ternary merge 块的 LOAD const + CALL AssertionError 路径
         与 ternary merge 块共享。
    """
    SOURCE_CODE = """assert x, (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
