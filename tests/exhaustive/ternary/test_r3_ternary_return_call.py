import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryReturnCall(ExhaustiveTestCase):
    """Bug R3-07: ternary 在 return + 函数调用 — 字节码不一致。

    原始:
        def f():
            return foo(a if cond else 0)
    缺陷: ternary 在 return + CALL 上下文中，
         merge_block 含 CALL + RETURN_VALUE，merge_context 未识别 return+call 场景。
    """
    SOURCE_CODE = """def f():
    return foo(a if cond else 0)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
