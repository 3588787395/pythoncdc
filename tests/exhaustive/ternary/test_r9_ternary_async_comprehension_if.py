import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryAsyncComprehensionIf(ExhaustiveTestCase):
    """Bug R9: async comprehension 的 if 条件是 ternary — 字节码不一致。

    原始:
        async def f():
            return [x async for x in iter if (a if c else b)]
    缺陷: async comprehension 的 if 条件位置使用 ternary。async for
         comprehension 的 GET_AITER + GET_ANEXT + SEND polling 嵌套
         ternary merge 块作为 if 条件，listcomp 内部 code object 的
         ternary 与外层 async 协议可能冲突。
    """
    SOURCE_CODE = """async def f():
    return [x async for x in iter if (a if c else b)]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
