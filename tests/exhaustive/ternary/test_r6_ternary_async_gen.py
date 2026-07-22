import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryAsyncGen(ExhaustiveTestCase):
    """Bug R6: async generator yield ternary — 字节码不一致。

    原始:
        async def g():
            yield (a if c else b)
    缺陷: async generator 函数中 yield 的是 ternary。期望 async gen code
         object 内部 ternary 正确归约为 Yield(IfExp)；当前疑似 async gen
         的 GET_AWAITABLE/SEND polling 与 ternary merge 块交互产生归属冲突。
    """
    SOURCE_CODE = """async def g():
    yield (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
