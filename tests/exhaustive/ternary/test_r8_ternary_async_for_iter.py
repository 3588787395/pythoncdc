import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryAsyncForIter(ExhaustiveTestCase):
    """Bug R8: async for iter 表达式是 ternary — 字节码不一致。

    原始:
        async def f():
            async for x in (a if c else b):
                pass
    缺陷: async for 的 iter 表达式是 ternary。R7-02 已知 async for
         body 内 ternary 失败。R8 测 iter 表达式变体：ternary merge
         块的 STORE 名称作为 GET_AITER 的源，async for 的 polling
         路径与 ternary entry/merge 块的归属关系可能冲突。
    """
    SOURCE_CODE = """async def f():
    async for x in (a if c else b):
        pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
