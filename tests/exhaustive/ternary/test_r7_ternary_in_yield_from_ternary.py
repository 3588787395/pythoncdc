import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInYieldFromTernary(ExhaustiveTestCase):
    """Bug R7: yield from (ternary) 嵌套 ternary 在 cause — 字节码不一致。

    原始:
        def g():
            x = yield from (a if c else b)
    缺陷: yield from (ternary) 后赋值给 x。R4 已测简单 yield from (ternary)
         (test_r4_ternary_in_yield_from)，R7 测 yield from (ternary) 的
         结果赋值给变量：GET_YIELD_FROM_ITER + SEND 循环后 STORE_NAME x
         消费 yield from 的最终返回值。该 STORE 与 ternary merge 块的
         STORE 不同，可能让 ternary 的 value_target 推断失败。
    """
    SOURCE_CODE = """def g():
    x = yield from (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
