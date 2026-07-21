import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryRoundKwargs(ExhaustiveTestCase):
    """Bug R15 (new): round(x, ndigits=(a if c else b)) — round kwarg ternary。

    原始:
        round(x, ndigits=(a if c else b))
    缺陷: ternary 作为 round 的 keyword 参数 ndigits=ternary。cond_block
         preload 含 PUSH_NULL + LOAD round + LOAD x + KW_NAMES + LOAD_CONST
         ('ndigits',)，ternary merge 块栈顶由 PRECALL + CALL 2 消费。
         R12 max_default 已测 max(x, default=ternary)，R15 测 round 同模式
         但不同内置。
    """
    SOURCE_CODE = """round(x, ndigits=(a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
