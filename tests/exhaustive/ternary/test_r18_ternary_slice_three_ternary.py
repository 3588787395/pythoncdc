import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR18TernarySliceThreeTernary(ExhaustiveTestCase):
    """Bug R18-01: x[(a if c else b):(d if e else f):(g if h else i)] — slice 三段均为 ternary。

    原始:
        x[(a if c else b):(d if e else f):(g if h else i)]
    缺陷: 单一 BINARY_SUBSCR 中 BUILD_SLICE 3 的 lower/upper/step 三个操作数
         都是 ternary。R14 slice_assign_both_bounds 已测两段 ternary (lower+upper)
         的 slice assign 失败，但三段 (含 step) 全为 ternary 的 subscript 表达式
         未覆盖。三个 ternary 的 merge 块与 BUILD_SLICE 消费链协调失败，
         反编译退化为三段独立 POP_TOP 表达式，字节码指令数不匹配 (16 vs 18)。
    """
    SOURCE_CODE = """x[(a if c else b):(d if e else f):(g if h else i)]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
