import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19AwaitInIfCond(ExhaustiveTestCase):
    # async 函数 if-elif-else 条件含 await + boolop + 比较：
    # async def f(a, b):
    #     if await a > 0 and await b < 100:
    #         return 'valid'
    #     elif await a == 0 or await b == 0:
    #         return 'zero'
    #     elif not await a:
    #         return 'falsy'
    #     else:
    #         return 'other'
    # 字节码 SEND / RESUME / YIELD_VALUE / GET_AWAITABLE / POP_JUMP_IF_FALSE
    # / 反编译器在 async if-elif-else 条件含 await + boolop + not 时易丢失 await。
    SOURCE_CODE = """async def f(a, b):
    if await a > 0 and await b < 100:
        return 'valid'
    elif await a == 0 or await b == 0:
        return 'zero'
    elif not await a:
        return 'falsy'
    else:
        return 'other'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
