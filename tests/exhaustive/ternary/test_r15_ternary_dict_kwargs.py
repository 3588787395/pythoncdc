import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryDictKwargs(ExhaustiveTestCase):
    """Bug R15 (new): dict(x=(a if c else b)) — dict constructor kwarg ternary。

    原始:
        dict(x=(a if c else b))
    缺陷: ternary 作为内置 dict() 的 keyword 参数 x=ternary。cond_block preload
         含 PUSH_NULL + LOAD dict + KW_NAMES + LOAD_CONST ('x',)，ternary merge
         块栈顶由 PRECALL + CALL 1 消费。R12 max_default 已测 max(x, default=
         ternary) 单 kwarg + 位置参数，R15 测 dict() 单 kwarg 无位置参数变体。
    """
    SOURCE_CODE = """dict(x=(a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
