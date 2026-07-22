import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInAsyncYield(ExhaustiveTestCase):
    """Bug R7: async generator yield (ternary) — 字节码不一致。

    原始:
        async def g():
            yield (a if c else b)
    缺陷: async generator yield ternary。R6 已测 async gen yield ternary
         (test_r6_ternary_async_gen)。R7 重测以确认 R6 修复是否覆盖：
         若 R6 已修复则本测试通过；若 R6 未覆盖某些边界则失败。
         期望：async gen code object 内 yield(IfExp) 正确归约。
    """
    SOURCE_CODE = """async def g():
    yield (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
