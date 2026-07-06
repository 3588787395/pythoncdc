"""异步嵌套函数测试 - 测试async/await与嵌套函数"""

import asyncio

# 测试1: 简单异步嵌套函数
async def outer_async(x):
    async def inner_async(y):
        await asyncio.sleep(0.01)
        return y * 2
    return await inner_async(x)

# 测试2: 异步闭包
async def make_async_adder(n):
    await asyncio.sleep(0.01)
    async def adder(x):
        await asyncio.sleep(0.01)
        return x + n
    return adder

# 测试3: 异步生成器嵌套
async def outer_async_gen():
    async def inner_async_gen(n):
        for i in range(n):
            await asyncio.sleep(0.01)
            yield i * 2
    return [x async for x in inner_async_gen(5)]

# 测试4: 异步上下文管理器中的嵌套函数
class AsyncContext:
    async def __aenter__(self):
        async def setup():
            await asyncio.sleep(0.01)
            return "setup"
        return await setup()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async def cleanup():
            await asyncio.sleep(0.01)
        await cleanup()

# 测试5: 混合同步异步嵌套
def outer_sync():
    async def inner_async():
        await asyncio.sleep(0.01)
        return "async result"
    return inner_async

# 测试6: 异步递归嵌套
async def async_factorial(n):
    async def compute(x):
        if x <= 1:
            return 1
        return x * await compute(x - 1)
    return await compute(n)
