import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernarySumStart(ExhaustiveTestCase):
    """Bug R15 (new): sum(x, start=(a if c else b)) — sum kwarg ternary。

    原始:
        sum(x, start=(a if c else b))
    缺陷: ternary 作为 sum 的 keyword 参数 start=ternary。cond_block preload
         含 PUSH_NULL + LOAD sum + LOAD x + KW_NAMES + LOAD_CONST ('start',)，
         ternary merge 块栈顶由 PRECALL + CALL 2 消费。R12 max_default 已测
         max(x, default=ternary)，R15 测 sum 同模式但内置不同（生成器消费型）。
    """
    SOURCE_CODE = """sum(x, start=(a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
