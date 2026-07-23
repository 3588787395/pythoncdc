import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryRaiseFromBothTernary(ExhaustiveTestCase):
    """Bug R19-05: raise (t1) from (t2) — raise 的异常与 cause 均为 ternary。

    原始:
        raise (a if c else b) from (d if e else f)
    缺陷: raise 语句的异常对象 (a if c else b) 与 cause (d if e else f) 都是
         ternary。R8 raise_from_ternary_cause 测过 `raise E from (ternary)`
         (异常常量，cause 是 ternary)，R14 raise_ternary_type_from 测过
         `raise (ternary) from E2` (异常 ternary，cause 常量)，R14 raise_arg_and_cause
         测过 `raise E(ternary) from (ternary)` (异常是 E(ternary) 调用，cause ternary)。
         本用例异常本身是裸 ternary (非 E(ternary) 调用)，且 cause 也是 ternary：
         两个 ternary merge 块先后汇聚到同一 RAISE_VARARGS 2，反编译退化为
         两段独立表达式语句 `(t1)` 与 `(t2)`，完全丢失 raise 语句结构。
    """
    SOURCE_CODE = """raise (a if c else b) from (d if e else f)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
