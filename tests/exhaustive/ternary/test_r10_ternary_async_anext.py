import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryAsyncAnext(ExhaustiveTestCase):
    """Bug R10: async generator + ternary in __anext__ (StopIteration.value) — 字节码不一致。

    原始:
        class C:
            async def __anext__(self):
                return (a if c else b)
    缺陷: __anext__ 方法体内 return (ternary)。ternary merge 块的
         RETURN_VALUE 与 async 函数的 SEND polling 循环可能冲突。
         R6 已测 async gen yield ternary；R10 测 __anext__ return ternary
         变体，验证 async 函数 return ternary 区域归约是否正确。
         依「父引用子入口」：父 Return 通过 merge_block 的 RETURN_VALUE
         引用 ternary 子节点作为返回值。
    """
    SOURCE_CODE = """class C:
    async def __anext__(self):
        return (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
