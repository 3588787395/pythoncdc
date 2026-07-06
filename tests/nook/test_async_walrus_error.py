"""
异步海象运算符错误实例

问题: 异步函数中的海象运算符有时会产生额外的await调用
"""

import asyncio

async def async_func():
    return 'result'

async def test_async_walrus():
    # 这个可能产生额外的await调用
    if (result := await async_func()) is not None:
        return result
    return None

async def test_multiple_async_walrus():
    # 多个异步海象运算符
    if (a := await async_func()) and (b := await async_func()):
        return a + b
    return 0
