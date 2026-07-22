import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInAsyncForElse(ExhaustiveTestCase):
    """Bug R7: async for-else 块中 ternary — 字节码不一致。

    原始:
        async def f():
            async for x in ys:
                pass
            else:
                y = a if c else b
    缺陷: async for-else 结构中，else 块包含 ternary 赋值。R7-02 已测
         async for body + ternary（ternary 退化为表达式泄漏 + 赋值丢失）。
         R7 测 async for-else 变体：else 块的入口（END_ASYNC_FOR 后）
         与 ternary entry 块的归属交互可能不同。
    """
    SOURCE_CODE = """async def f():
    async for x in ys:
        pass
    else:
        y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
