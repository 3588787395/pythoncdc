import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryAssertTwoTernariesBoolop(ExhaustiveTestCase):
    """Bug R14 (new): assert (a if c else b) and (d if e else f) — assert 两 ternary + boolop。

    原始:
        assert (a if c else b) and (d if e else f)
    缺陷: assert 测试表达式是两个 ternary 通过 boolop AND 组合。R7/R8 已测 assert
         ternary msg。R14 测 assert 测试是 boolop(ternary, ternary) 变体：两个 ternary
         region 同时归约，第一个 ternary merge 之后 LOAD 短路测试 + 第二个 ternary
         merge + POP_JUMP_IF_TRUE 跳过 RAISE_VARARGS 1 (AssertionError)。
    """
    SOURCE_CODE = """assert (a if c else b) and (d if e else f)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
