import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20AsyncGeneratorInIfBody(ExhaustiveTestCase):
    # if body 内含 async generator 函数定义 + 调用 + async for：
    # async def f(flag, items):
    #     if flag:
    #         async def gen(seq):
    #             for x in seq:
    #                 yield x * 2
    #         result = []
    #         async for y in gen(items):
    #             result.append(y)
    #         return result
    #     return []
    # 字节码 GET_AITER / GET_ANEXT / END_ASYNC_FOR / YIELD_VALUE
    # / 反编译器在 if body 内 async generator + async for 时易丢失 yield 或 async for 结构。
    SOURCE_CODE = """async def f(flag, items):
    if flag:
        async def gen(seq):
            for x in seq:
                yield x * 2
        result = []
        async for y in gen(items):
            result.append(y)
        return result
    return []"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
