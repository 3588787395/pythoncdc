# async gather pattern
import asyncio
async def coro1():
    return 1
async def coro2():
    return 2
async def gather_results():
    results = await asyncio.gather(coro1(), coro2())
    return results
