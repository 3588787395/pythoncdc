import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryDictLiteralKeyValueTernary(ExhaustiveTestCase):
    """Bug R19-12: {(t1): (t2)} — dict literal 的 key 与 value 均为 ternary。

    原始:
        x = {(a if c else b): (d if e else f)}
    缺陷: dict literal `{key: value}` 的 key 和 value 都是 ternary。R18
         dictcomp_key_value_ternary 测过 dict comprehension `{(t1): (t2) for k in y}`
         (MAP_ADD 消费)。本用例是 dict literal (BUILD_MAP 消费)：BUILD_MAP 1
         消费栈顶 value (t2) 与次栈顶 key (t1)，两个 ternary merge 块先后
         汇聚到同一 BUILD_MAP，反编译退化为独立表达式 `(t1)`，丢失 value
         ternary 与 dict literal 结构。
    """
    SOURCE_CODE = """x = {(a if c else b): (d if e else f)}
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
