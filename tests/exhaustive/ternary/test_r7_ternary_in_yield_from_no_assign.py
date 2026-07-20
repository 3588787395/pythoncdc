import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInYieldFromNoAssign(ExhaustiveTestCase):
    """Bug R7: yield from (ternary) 不赋值 — 字节码不一致。

    原始:
        def g():
            yield from (a if c else (b if d else e))
    缺陷: yield from 嵌套 ternary，无赋值。R7-06 已测 yield from (ternary)
         + 赋值变体（ternary 退化为泄漏表达式 + yield from 只取 true_value）。
         R7 测嵌套 ternary + 无赋值变体：嵌套 ternary 的内部归约 +
         yield from 的栈消费可能让最外层 merge 块的归属更复杂。
    """
    SOURCE_CODE = """def g():
    yield from (a if c else (b if d else e))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
