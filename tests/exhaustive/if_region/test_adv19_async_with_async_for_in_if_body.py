import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19AsyncWithAsyncForInIfBody(ExhaustiveTestCase):
    # if body 内含 async with + async for + await + 嵌套 if（async 函数）：
    # async def f(flag):
    #     if flag:
    #         async with get_session() as session:
    #             async for item in session.iter():
    #                 if item.is_valid():
    #                     await process(item)
    #                     return 'done'
    #         return 'no_item'
    #     return 'skip'
    # 字节码 BEFORE_ASYNC_WITH / SETUP_ASYNC_WITH / GET_AITER / GET_ANEXT / END_ASYNC_FOR
    # / 反编译器在 async 函数 if body 内 async with + async for + 嵌套 if 时易结构错乱。
    SOURCE_CODE = """async def f(flag):
    if flag:
        async with get_session() as session:
            async for item in session.iter():
                if item.is_valid():
                    await process(item)
                    return 'done'
        return 'no_item'
    return 'skip'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
