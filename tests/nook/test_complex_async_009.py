# 复杂异步测试
import asyncio

async def complex_async_function():
    """复杂的异步函数"""
    result = []
    
    # 并发执行多个任务
    tasks = []
    for i in range(3):
        task = asyncio.create_task(async_task(i))
        tasks.append(task)
    
    # 等待所有任务完成
    for task in tasks:
        result.append(await task)
    
    return result

async def async_task(n):
    """异步任务"""
    await asyncio.sleep(0.01)
    return n * 2

async def async_with_context():
    """使用异步上下文管理器"""
    async with AsyncContext() as ctx:
        return await ctx.process()

class AsyncContext:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def process(self):
        return "processed"
