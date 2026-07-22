import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernarySubscrTargetAndValue(ExhaustiveTestCase):
    """Bug R17-02: x[a if c else b] = (d if e else f) — ternary in subscr target AND value。

    原始:
        x[a if c else b] = (d if e else f)
    缺陷: 同一 STORE_SUBSCR 语句中，下标 target 是 ternary，赋值 value 也是
         ternary。两个 ternary 共享/相邻 merge 块，反编译器对
         subscript-target ternary 的归约与 value ternary 协调失败，字节码
         指令数不匹配 (11 vs 14)。
    """
    SOURCE_CODE = """x[a if c else b] = (d if e else f)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
