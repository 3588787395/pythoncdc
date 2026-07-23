import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR18TernaryDictcompKeyValueTernary(ExhaustiveTestCase):
    """Bug R18-07: {(a if c else b): (d if e else f) for k in y} — dictcomp key 与 value 均为 ternary。

    原始:
        x = {(a if c else b): (d if e else f) for k in y}
    缺陷: dict comprehension 的 key 和 value 都是 ternary。R6 dictcomp_complex
         测过 value 为 ternary (key 是简单变量)。本用例 key 也是 ternary：
         MAP_ADD 消费栈顶 (value) 与次栈顶 (key)，两个 ternary 的 merge 块
         先后汇聚到同一 MAP_ADD。反编译丢失 key ternary (保留 value ternary)，
         字节码指令数不匹配 (12 vs 10)。
    """
    SOURCE_CODE = """x = {(a if c else b): (d if e else f) for k in y}
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
