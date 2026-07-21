import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryDictFromkeys(ExhaustiveTestCase):
    """Bug R15 (new): dict.fromkeys((a if c else b), x) — Constant obj.method (dict.fromkeys)。

    原始:
        dict.fromkeys((a if c else b), x)
    缺陷: ternary 作为 dict.fromkeys 第一参数（iterable），x 作为第二参数
         （value）。cond_block preload 含 LOAD dict + LOAD_ATTR fromkeys，
         ternary merge 块栈顶与 LOAD x 一起 PRECALL + CALL 2 消费。
         验证 dict 类型对象的 class method 调用 + ternary 参数变体。
    """
    SOURCE_CODE = """dict.fromkeys((a if c else b), x)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
