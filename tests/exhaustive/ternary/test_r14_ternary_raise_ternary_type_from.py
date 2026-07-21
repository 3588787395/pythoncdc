import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryRaiseTernaryTypeFrom(ExhaustiveTestCase):
    """Bug R14 (new): raise (a if c else b) from E2 — raise 异常类型是 ternary。

    原始:
        raise (a if c else b) from E2
    缺陷: raise from 的异常类型本身是 ternary，cause 是固定 E2。R3 测 raise_from，
         R8 测 raise_from_ternary_cause（cause 是 ternary）。R14 测反方向变体：
         exception 类型是 ternary。RAISE_VARARGS 2 第一个参数 = ternary merge 块栈顶，
         第二个 = LOAD_NAME E2 preload。注意 R7 raise_no_from 已测 raise (ternary)，
         R14 加 from E2 后缀测试 from 子句与 ternary exception 共存。
    """
    SOURCE_CODE = """raise (a if c else b) from E2
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
