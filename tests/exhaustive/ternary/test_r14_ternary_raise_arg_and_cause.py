import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryRaiseArgAndCause(ExhaustiveTestCase):
    """Bug R14 (new): raise E(a if c else b) from (d if e else f) — 两处 ternary。

    原始:
        raise E(a if c else b) from (d if e else f)
    缺陷: raise 同时含两个 ternary：第一个 ternary 在 E() 调用 args，第二个 ternary
         在 from cause 位置。R7 raise_from_complex 已测 raise E + ternary arg，
         R8 测 raise from ternary cause。R14 测两个 ternary 共存场景：两个 ternary
         region 同时归约，分别作为 E() 调用参数与 RAISE_VARARGS 2 第二参数。
         可能出现 chained ternary 识别冲突。
    """
    SOURCE_CODE = """raise E(a if c else b) from (d if e else f)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
