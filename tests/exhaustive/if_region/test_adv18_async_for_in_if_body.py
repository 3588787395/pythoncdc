import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18AsyncForInIfBody(ExhaustiveTestCase):
    # if body 内含 async for + async with + await 复合结构：
    # async def f():
    #     if flag:
    #         async for x in gen():
    #             if x > 0:
    #                 await process(x)
    #             else:
    #                 continue
    #         return 1
    #     return 0
    # 字节码 GET_AITER / GET_ANEXT / SEND + 内嵌 if + await / 反编译器
    # 在 if body 内 async for + 嵌套 if-else 时易把 await 错挂到 async for 外。
    SOURCE_CODE = """async def f():
    if flag:
        async for x in gen():
            if x > 0:
                await process(x)
            else:
                continue
        return 1
    return 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
