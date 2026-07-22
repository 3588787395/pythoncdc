import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryAssertTestWithMsg(ExhaustiveTestCase):
    """Bug R14 (new): assert (a if c else b), 'msg' — assert 测试是 ternary + 带消息。

    原始:
        assert (a if c else b), 'msg'
    缺陷: assert 的测试表达式是 ternary，且带消息字符串。R4/R7/R8 已测 assert
         ternary msg 变体。R14 测 assert 测试本身是 ternary + 简单消息字符串
         变体：ternary merge 块栈顶经 POP_JUMP_IF_TRUE 跳过 RAISE_VARARGS 2
         (AssertionError + 'msg')。test 与 msg 共存场景。
    """
    SOURCE_CODE = """assert (a if c else b), 'msg'
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
