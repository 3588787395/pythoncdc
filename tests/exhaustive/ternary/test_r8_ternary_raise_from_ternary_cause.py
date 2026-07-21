import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryRaiseFromTernaryCause(ExhaustiveTestCase):
    """Bug R8: raise E from (ternary) — cause 是 ternary — 字节码不一致。

    原始:
        raise E from (a if c else b)
    缺陷: raise from 的 cause 是 ternary。R3 已测过 ternary_raise_from。
         R8 测变体确认是否仍稳定：ternary merge 块的栈输出作为 RAISE_VARARGS 2
         的第二个参数，与 LOAD E 的 preload 顺序可能冲突。
    """
    SOURCE_CODE = """raise E from (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
