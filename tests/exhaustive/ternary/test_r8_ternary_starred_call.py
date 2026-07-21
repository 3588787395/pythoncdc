import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryStarredCall(ExhaustiveTestCase):
    """Bug R8: call 中 starred(ternary) — 字节码不一致。

    原始:
        f(*(a if c else b))
    缺陷: 函数调用中 starred 表达式是 ternary。R5 已测 ternary
         in call_starred 但变体不同。R8 测单一 starred arg 变体：
         BUILD_LIST 0 + LIST_EXTEND 1（消费 ternary）+ CALL 1
         在 merge_block 与 ternary merge 的栈消费顺序可能冲突。
    """
    SOURCE_CODE = """f(*(a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
