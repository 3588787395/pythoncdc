import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20AsyncForWithAwaitInIfBody(ExhaustiveTestCase):
    # if-elif-else body 内含 async for + await + async with 组合：
    # async def f(flag, urls):
    #     if flag == 'fetch':
    #         results = []
    #         async for url in urls:
    #             response = await fetch(url)
    #             if response.status == 200:
    #                 results.append(await response.text())
    #             else:
    #                 results.append(None)
    #         return results
    #     elif flag == 'context':
    #         async with session() as s:
    #             return await s.get('key')
    #     else:
    #         return []
    # 字节码 GET_AITER / GET_ANEXT / END_ASYNC_FOR / BEFORE_WITH
    # / 反编译器在 if-elif-else 三分支都含 async 组合时易丢失 async for 结构。
    SOURCE_CODE = """async def f(flag, urls):
    if flag == 'fetch':
        results = []
        async for url in urls:
            response = await fetch(url)
            if response.status == 200:
                results.append(await response.text())
            else:
                results.append(None)
        return results
    elif flag == 'context':
        async with session() as s:
            return await s.get('key')
    else:
        return []"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
