import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernaryListcompBodyAndIf(ExhaustiveTestCase):
    """Bug R17-07: x = [(a if c else b) for x in y if (d if e else f)] — listcomp body+if both ternary。

    原始:
        x = [(a if c else b) for x in y if (d if e else f)]
    缺陷: list comprehension 中 body 表达式和 if 条件都是 ternary。两个 ternary
         嵌套在 comprehension 的 code object 内，merge 块与 comprehension 的
         FOR_ITER/JUMP_BACKWARD 边界冲突。R9 listcomp_condition 测过 if 条件
         为 ternary，R6 listcomp_complex 测过 body 为 ternary，但两者同时存在
         未覆盖，字节码指令数不匹配 (12 vs 10)。
    """
    SOURCE_CODE = """x = [(a if c else b) for x in y if (d if e else f)]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
