import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryCallableNoArgs(ExhaustiveTestCase):
    """Bug R15 (new): (a if c else b)() — ternary as callable no args。

    原始:
        (a if c else b)()
    缺陷: ternary 作为可调用对象，无参数调用。cond_block preload 含 PUSH_NULL
         （Python 3.11+ 隐式 NULL），ternary merge 块栈顶作为 CALL 的 callable，
         由 PRECALL + CALL 0 消费。验证 ternary as callable + 0 参数变体。
    """
    SOURCE_CODE = """(a if c else b)()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
